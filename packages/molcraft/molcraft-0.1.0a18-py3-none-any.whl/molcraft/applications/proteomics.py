import re
import keras
import numpy as np
import tensorflow as tf
import tensorflow_text as tf_text
from rdkit import Chem

from molcraft import featurizers
from molcraft import tensors
from molcraft import layers
from molcraft import models 
from molcraft import chem

"""






No need to correct smiles for modeling, only for interpretation.

Use added smiles data to rearrange list of saliency values. 












"""

# TODO: Add regex pattern for residue (C-term mod + N-term mod)?
# TODO: Add regex pattern for residue (C-term mod + N-term mod + mod)?

no_mod_pattern = r'([A-Z])'
side_chain_mod_pattern = r'([A-Z]\[[A-Za-z0-9]+\])'
n_term_mod_pattern = r'(\[[A-Za-z0-9]+\]-[A-Z])'
c_term_mod_pattern = r'([A-Z]-\[[A-Za-z0-9]+\])'
side_chain_and_n_term_mod_pattern = r'(\[[A-Za-z0-9]+\]-[A-Z]\[[A-Za-z0-9]+\])'
side_chain_and_c_term_mod_pattern = r'([A-Z]\[[A-Za-z0-9]+\]-\[[A-Za-z0-9]+\])'

residue_pattern: str = "|".join([
    side_chain_and_n_term_mod_pattern,
    side_chain_and_c_term_mod_pattern,
    n_term_mod_pattern,
    c_term_mod_pattern,
    side_chain_mod_pattern,
    no_mod_pattern
])

default_residues: dict[str, str] = {
    "A": "N[C@@H](C)C(=O)O",
    "C": "N[C@@H](CS)C(=O)O",
    "D": "N[C@@H](CC(=O)O)C(=O)O",
    "E": "N[C@@H](CCC(=O)O)C(=O)O",
    "F": "N[C@@H](Cc1ccccc1)C(=O)O",
    "G": "NCC(=O)O",
    "H": "N[C@@H](CC1=CN=C-N1)C(=O)O",
    "I": "N[C@@H](C(CC)C)C(=O)O",
    "K": "N[C@@H](CCCCN)C(=O)O",
    "L": "N[C@@H](CC(C)C)C(=O)O",
    "M": "N[C@@H](CCSC)C(=O)O",
    "N": "N[C@@H](CC(=O)N)C(=O)O",
    "P": "N1[C@@H](CCC1)C(=O)O",
    "Q": "N[C@@H](CCC(=O)N)C(=O)O",
    "R": "N[C@@H](CCCNC(=N)N)C(=O)O",
    "S": "N[C@@H](CO)C(=O)O",
    "T": "N[C@@H](C(O)C)C(=O)O",
    "V": "N[C@@H](C(C)C)C(=O)O",
    "W": "N[C@@H](CC(=CN2)C1=C2C=CC=C1)C(=O)O",
    "Y": "N[C@@H](Cc1ccc(O)cc1)C(=O)O",
}

def has_c_terminal_mod(residue: str):
    if re.search(c_term_mod_pattern, residue):
        return True 
    return False 

def has_n_terminal_mod(residue: str):
    if re.search(n_term_mod_pattern, residue):
        return True 
    return False 

# def register_residues(residues: dict[str, str]) -> None:
#     for residue, smiles in residues.items():
#         if residue.startswith('P'):
#             smiles.startswith('N'), f'Incorrect SMILES permutation for {residue}.'
#         elif not residue.startswith('['):
#             smiles.startswith('N[C@@H]'), f'Incorrect SMILES permutation for {residue}.'
#         if len(residue) > 1 and not residue[1] == "-":
#             assert smiles.endswith('C(=O)O'), f'Incorrect SMILES permutation for {residue}.'
#         registered_residues[residue] = smiles
#         registered_residues[residue + '*'] = smiles.strip('O')
    
    
class Peptide(chem.Mol):

    @classmethod
    def from_sequence(cls, sequence: str, **kwargs) -> 'Peptide':
        sequence = [
            match.group(0) for match in re.finditer(residue_pattern, sequence)
        ]
        peptide_smiles = []
        for i, residue in enumerate(sequence):
            if i < len(sequence) - 1:
                residue_smiles = registered_residues[residue + '*']
            else:
                residue_smiles = registered_residues[residue]
            peptide_smiles.append(residue_smiles)
        peptide_smiles = ''.join(peptide_smiles)
        return super().from_encoding(peptide_smiles, **kwargs)


def permute_residue_smiles(smiles: str) -> str:
    glycine = chem.Mol.from_encoding("NCC(=O)O")
    mol = chem.Mol.from_encoding(smiles)
    nitrogen_index = mol.GetSubstructMatch(glycine)[0]
    permuted_smiles = Chem.MolToSmiles(
        mol, rootedAtAtom=nitrogen_index
    )
    return permuted_smiles

def check_peptide_residue_smiles(smiles: list[str]) -> bool:
    backbone = 'NCC(=O)' * (len(smiles) - 1) + 'NC'
    backbone = chem.Mol.from_encoding(backbone)
    mol = chem.Mol.from_encoding(''.join(smiles))
    is_valid = mol.HasSubstructMatch(backbone)
    return is_valid

@keras.saving.register_keras_serializable(package='proteomics')
class ResidueEmbedding(keras.layers.Layer):

    def __init__(
        self, 
        featurizer: featurizers.MolGraphFeaturizer,
        embedder: models.GraphModel, 
        residues: dict[str, str] | None = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        if residues is None:
            residues = {}
        self.embedder = embedder
        self.featurizer = featurizer
        self.embedding_dim = int(self.embedder.output.shape[-1])
        self.ragged_split = SequenceSplitter(pad=False)
        self.split = SequenceSplitter(pad=True)
        self.use_cached_embeddings = tf.Variable(False)
        self.residues = residues
        self.supports_masking = True
        
    @property
    def residues(self) -> dict[str, str]:
        return self._residues

    @residues.setter
    def residues(self, residues: dict[str, str]) -> None:
        
        residues = {**default_residues, **residues}
        self._residues = {}
        for residue, smiles in residues.items():
            permuted_smiles = permute_residue_smiles(smiles)
            # Returned smiles should begin with the amino group.
            # It seems that the returned smiles ends with carboxyl group,
            # though we do another check just in case. 
            if not has_c_terminal_mod(residue):
                carboxyl_group = 'C(=O)O'
                if not permuted_smiles.endswith(carboxyl_group):
                    raise ValueError(
                        f'Unsupported permutation of {residue!r} smiles: {permuted_smiles!r}.'
                    )
            self._residues[residue] = permuted_smiles
            self._residues[residue + '*'] = permuted_smiles.rstrip('O')

        residue_keys = sorted(self._residues.keys())
        residue_values = range(len(residue_keys))
        residue_oov_value = np.where(np.array(residue_keys) == "G")[0][0]

        self.mapping = tf.lookup.StaticHashTable(
            tf.lookup.KeyValueTensorInitializer(
                keys=residue_keys, 
                values=residue_values
            ),
            default_value=residue_oov_value,
        )

        self.graph = tf.stack([
            self.featurizer(self._residues[r]) for r in residue_keys
        ], axis=0)

        zeros = tf.zeros((residue_values[-1] + 1, self.embedding_dim))
        self.cached_embeddings = tf.Variable(initial_value=zeros)
        _ = self.cache_and_get_embeddings()

    def build(self, input_shape) -> None:
        self.residues = self._residues
        super().build(input_shape)

    def call(self, sequences: tf.Tensor, training: bool = None) -> tf.Tensor:
        if training is False:
            self.use_cached_embeddings.assign(True)
        else:
            self.use_cached_embeddings.assign(False)
        embeddings = tf.cond(
            pred=self.use_cached_embeddings,
            true_fn=lambda: self.cached_embeddings,
            false_fn=lambda: self.cache_and_get_embeddings(),
        )
        sequences = self.ragged_split(sequences)
        sequences = keras.ops.concatenate([
            tf.strings.join([sequences[:, :-1], '*']), sequences[:, -1:]
        ], axis=1)
        indices = self.mapping.lookup(sequences)
        return tf.gather(embeddings, indices).to_tensor()
    
    def cache_and_get_embeddings(self) -> tf.Tensor:
        embeddings = self.embedder(self.graph)
        self.cached_embeddings.assign(embeddings)
        return embeddings
    
    def compute_mask(
        self, 
        inputs: tensors.GraphTensor, 
        mask: bool | None = None
    ) -> tf.Tensor | None:
        sequences = self.split(inputs)
        return keras.ops.not_equal(sequences, '')
                
    def get_config(self) -> dict:
        config = super().get_config()
        config.update({
            'featurizer': keras.saving.serialize_keras_object(
                self.featurizer
            ),
            'embedder': keras.saving.serialize_keras_object(
                self.embedder
            ),
            'residues': self._residues,
        })
        return config
    
    @classmethod
    def from_config(cls, config: dict) -> 'ResidueEmbedding':
        config['featurizer'] = keras.saving.deserialize_keras_object(
            config['featurizer']
        )
        config['embedder'] = keras.saving.deserialize_keras_object(
            config['embedder']
        )
        return super().from_config(config)
    

@keras.saving.register_keras_serializable(package='proteomics')
class SequenceSplitter(keras.layers.Layer): 

    def __init__(self, pad: bool, **kwargs):
        super().__init__(**kwargs)
        self.pad = pad 

    def call(self, inputs: tf.Tensor) -> tf.Tensor | tf.RaggedTensor:
        inputs = tf_text.regex_split(inputs, residue_pattern, residue_pattern)
        if self.pad:
            inputs = inputs.to_tensor()
        return inputs
    

# registered_residues: dict[str, str] = {}
# register_residues(default_residues)
