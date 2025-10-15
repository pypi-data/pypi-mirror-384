"""
Copyright © 2025 Legendary Requirements

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from enum import Enum
from io import BufferedIOBase
from itertools import islice, repeat
from typing import Any, Iterable, Iterator

from .json import JSONBase64Decoder, JSONBase64Encoder, JSONHexDecoder, JSONHexEncoder
from .utility import BITS, HASH_BIT_LENGTH, HASH_BYTE_LENGTH, IOBytesIterator, OUTER_BIT, block_hash, \
    hash_to_int, hashes_equal, int_to_hash


class _ValidationState(Enum):
    """
    Validation state.
    """

    Pending = 0
    """
    Pending (incomplete).
    """

    Valid = 1
    """
    Valid (complete).
    """

    Invalid = 2
    """
    Invalid (complete).
    """


class _Validator(ABC):
    """
    Validator.
    """

    @abstractmethod
    def _validate_additional(self, node_index: int, partial_proof: _SMTPartialProof) -> _ValidationState:
        """
        Callback to perform additional validation.

        :param node_index:
        Node index.

        :param partial_proof:
        Partial proof.

        :return:
        Validation state.
        """

        pass

    def __finalize_padding(self, left_pad: list[int], right_pad: list[int], hash: bytes) -> bytes:
        """
        Finalize padding if padded.

        :param left_pad:
        Left pad.

        :param right_pad:
        Right pad.

        :param hash:
        Hash.

        :return:
        Hash of padded input hash if padded or input hash if not.
        """
        if len(left_pad) != 0 or len(right_pad) != 0:
            hash_pad = block_hash(bytes(left_pad), hash, bytes(right_pad))

            # Reset padded state.
            left_pad.clear()
            right_pad.clear()
        else:
            hash_pad = hash

        return hash_pad

    def validate(self, index: int, candidate_hash: bytes, root_hash: bytes, proof: SMTProof) -> bool:
        """
        Determine if proof is valid.

        :param index:
        Index.

        :param candidate_hash:
        Candidate hash to validate.

        :param root_hash:
        Root hash.

        :param proof:
        Proof.

        :return:
        True if valid.
        """

        node_index = index

        node_hash = candidate_hash

        node_converge = proof.converge

        hashes = proof.hashes
        hash_index = 0

        left_pad: list[int] = []
        right_pad: list[int] = []

        validation_state = _ValidationState.Pending

        i = 0

        while validation_state == _ValidationState.Pending and i < HASH_BIT_LENGTH:
            is_left = node_index & 1 == 0

            # Prepare to move up to parent node.
            node_index >>= 1

            converge_bit = BITS[i]

            if node_converge & converge_bit != 0:
                # Turn off converge bit for parent node.
                node_converge ^= converge_bit

                node_hash = self.__finalize_padding(left_pad, right_pad, node_hash)

                if hash_index < len(hashes):
                    peer_hash = hashes[hash_index]
                    
                    hash_index += 1

                    node_hash = block_hash(node_hash, peer_hash) if is_left else block_hash(peer_hash, node_hash)

                    # Additional validation is performed with parent values.
                    validation_state = self._validate_additional(node_index, _SMTPartialProof(node_hash, node_converge, hashes[hash_index:]))
                else:
                    # Not enough hashes.
                    validation_state = _ValidationState.Invalid
            else:
                depth = HASH_BIT_LENGTH - i - 1

                if is_left:
                    right_pad.append(depth)
                else:
                    left_pad.insert(0, depth)

            i += 1

        node_hash = self.__finalize_padding(left_pad, right_pad, node_hash)

        # If validation state is still pending, perform final check of hashes length and root hash.
        if validation_state == _ValidationState.Pending:
            validation_state = _ValidationState.Valid if hash_index == len(hashes) and hashes_equal(node_hash, root_hash) else _ValidationState.Invalid

        return validation_state == _ValidationState.Valid


class _SingleValidator(_Validator):
    """
    Validator for a single proof.
    """

    def _validate_additional(self, node_index: int, partial_proof: _SMTPartialProof) -> _ValidationState:
        # Nothing additional to do.
        return _ValidationState.Pending


_single_validator = _SingleValidator()
"""
Single validator instance; single validator is stateless so only one instance is required.
"""


class SMTProofCandidate:
    """
    Candidate for SMT proof.
    """

    def __init__(self, index: int, hash: bytes, proof: SMTProof, additional: Any = None):
        """
        Constructor.

        :param index:
        Index into SMT.

        :param hash:
        Hash at index.

        :param proof:
        Proof.

        :param additional:
        Additional data to pass through to result.
        """

        self._index = index
        self._hash = hash
        self._proof = proof
        self._additional = additional

    @property
    def index(self) -> int:
        """
        Get the index into the SMT.
        """

        return self._index

    @property
    def hash(self) -> bytes:
        """
        Get the hash at index.
        """

        return self._hash

    @property
    def proof(self) -> SMTProof:
        """
        Get the proof.
        """

        return self._proof

    @property
    def additional(self) -> Any:
        """
        Get the additional data to pass through to result.
        """

        return self._additional


class SMTProofResult:
    """
    Result of SMT proof.
    """

    def __init__(self, index: int, valid: bool, additional: Any):
        """
        Constructor.

        :param index:
        Index into SMT.

        :param valid:
        True if proof is valid.

        :param additional:
        Additional data passed through from candidate.
        """

        self._index = index
        self._valid = valid
        self._additional = additional

    @property
    def index(self)-> int:
        """
        Get the index into the SMT.
        """

        return self._index

    @property
    def valid(self) -> bool:
        """
        Determine if proof is valid.
        """

        return self._valid

    @property
    def additional(self) -> Any:
        """
        Get the additional data passed through from candidate.
        """

        return self._additional


class _SMTPartialProof:
    """
    Partial proof for batch validation.
    """

    def __init__(self, hash: bytes, converge: int, hashes: list[bytes]):
        """
        Constructor.

        :param hash:
        Hash at the node at which the partial proof applies (root hash at root node).

        :param converge:
        Bitmap of converged nodes remaining on the path to the root (0 at root node).

        :param hashes:
        Remaining hashes at converged nodes on the path to the root (empty at root node).
        """

        self._hash = hash
        self._converge = converge
        self._hashes = hashes

    @property
    def hash(self)-> bytes:
        """
        Get the hash at the node at which the partial proof applies
        """

        return self._hash

    @property
    def converge(self) -> int:
        """
        Get the bitmap of converged nodes remaining on the path to the root.
        """

        return self._converge

    @property
    def hashes(self) -> list[bytes]:
        """
        Get the remaining hashes at converged nodes on the path to the root
        """

        return self._hashes


class _BatchValidator(_Validator, Iterable[SMTProofResult]):
    """
    Validator for a batch of proofs.
    """

    def __init__(self, candidates: Iterable[SMTProofCandidate], root_hash: bytes):
        """
        Constructor.

        :param candidates:
        Candidates to validate.

        :param root_hash:
        Root hash.
        """

        super().__init__()

        self._candidates_iterator = iter(candidates)

        self._root_hash = root_hash

        self._partial_proofs_cache = dict[int, _SMTPartialProof]()

        self._added_node_indexes = list[int]()

    def _validate_additional(self, node_index: int, partial_proof: _SMTPartialProof) -> _ValidationState:
        valid_partial_proof = self._partial_proofs_cache.get(node_index)

        if valid_partial_proof is None:
            # It's likely that most validations will succeed so assume partial proof is valid.
            self._partial_proofs_cache[node_index] = partial_proof

            self._added_node_indexes.append(node_index)

            validation_state = _ValidationState.Pending
        else:
            # Terminate early by comparing provided partial proof with known valid partial proof.
            validation_state = _ValidationState.Valid if \
                hashes_equal(partial_proof.hash, valid_partial_proof.hash) and \
                partial_proof.converge == valid_partial_proof.converge and \
                partial_proof.hashes == valid_partial_proof.hashes \
                else _ValidationState.Invalid

        return validation_state

    def __iter__(self):
        return self

    def __next__(self) -> SMTProofResult:
        candidate = next(self._candidates_iterator)

        index = candidate.index

        # Adding the outer bit to the index prevents values on the lower left of the tree from being confused with those on the upper right.
        valid = self.validate(index | OUTER_BIT, candidate.hash, self._root_hash, candidate.proof)

        if not valid:
            # Remove newly added partial proofs.
            for added_node_index in self._added_node_indexes:
                self._partial_proofs_cache.pop(added_node_index)

        self._added_node_indexes.clear()

        return SMTProofResult(index, valid, candidate.additional)


class _SMTProofJSONHexEncoder(JSONHexEncoder):
    """
    Hexadecimal encoder for JSON export of SMT proof.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        :param args:
        Additional arguments.

        :param kwargs:
        Additional arguments.
        """

        super().__init__(["converge"], *args, **kwargs)


class _SMTProofJSONBase64Encoder(JSONBase64Encoder):
    """
    Base64 encoder for JSON export of SMT proof.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        :param args:
        Additional arguments.

        :param kwargs:
        Additional arguments.
        """

        super().__init__(["converge"], *args, **kwargs)


class SMTProof:
    """
    SMT proof.
    """

    def __init__(self, converge: int, hashes: list[bytes]):
        """
        Constructor.

        :param converge:
        Bitmap of converged nodes.

        :param hashes:
        Hashes at converged nodes.
        """

        self._converge = converge
        self._hashes = hashes

    @property
    def converge(self) -> int:
        """
        Get the bitmap of converged nodes.
        """

        return self._converge

    @property
    def hashes(self) -> list[bytes]:
        """
        Get the hashes at converged nodes.
        """

        return self._hashes

    def is_valid(self, index: int, candidate_hash: bytes, root_hash: bytes) -> bool:
        """
        Determine if proof is valid.

        :param index:
        Index.

        :param candidate_hash:
        Candidate hash to validate.

        :param root_hash:
        Root hash.

        :return:
        True if proof is valid.
        """

        return _single_validator.validate(index, candidate_hash, root_hash, self)

    @staticmethod
    def is_valid_batch(candidates: Iterable[SMTProofCandidate], root_hash: bytes) -> Iterable[SMTProofResult]:
        """
        Determine if proofs are valid.

        :param candidates:
        Candidates to validate.

        :param root_hash:
        Root hash.

        :return:
        Iterable containing index and validity status.
        """

        return _BatchValidator(candidates, root_hash)

    def to_json(self, base64 = False, compact = True) -> str:
        """
        Export the SMT proof to JSON.

        :param base64:
        If true, exports values using base64 instead of hexadecimal.

        :param compact:
        If true, exports in compact form (no extra space or line breaks).

        :return:
        JSON.
        """

        return json.dumps({
            "converge": self._converge,
            "hashes": self._hashes
        }, cls = _SMTProofJSONHexEncoder if not base64 else _SMTProofJSONBase64Encoder, indent = None if compact else 2)

    @staticmethod
    def from_json(s: str, base64 = False) -> "SMTProof":
        """
        Import an SMT proof from JSON.

        :param s:
        JSON.

        :param base64:
        imports values using base64 instead of hexadecimal.

        :return:
        SMT proof.
        """

        raw_object = json.loads(s, object_hook = (JSONHexDecoder if not base64 else JSONBase64Decoder)(["hashes"], [], ["converge"]).decode)

        if not isinstance(raw_object, dict) or "converge" not in raw_object or "hashes" not in raw_object:
            raise ValueError("Invalid string content")

        return SMTProof(raw_object["converge"], raw_object["hashes"])

    def to_binary(self) -> bytes:
        """
        Export the SMT proof to binary.

        :return:
        Binary data.
        """

        converge_binary = int_to_hash(self.converge)

        converge_zero_bytes_count = 0

        # Most trees are very shallow so the converge bitmap will be mostly leading 0x00 bytes.
        while converge_zero_bytes_count < HASH_BYTE_LENGTH and converge_binary[converge_zero_bytes_count] == 0x00:
            converge_zero_bytes_count += 1

        hashes = self.hashes
        hashes_length = len(hashes)

        binary = bytearray()

        binary.append(converge_zero_bytes_count)
        binary.extend(converge_binary[converge_zero_bytes_count:])
        binary.append(hashes_length)

        for hash in hashes:
            binary.extend(hash)

        return binary


    @staticmethod
    def from_binary(source: Iterable[int] | Iterator[int] | BufferedIOBase) -> "SMTProof":
        """
        Import an SMT proof from binary.

        :param source:
        Binary source.

        :return:
        SMT proof.
        """

        source_iterator = iter(source) if not isinstance(source, BufferedIOBase) else IOBytesIterator(source)
        
        converge_zero_bytes_count = next(source_iterator)

        converge_binary = bytearray()

        # Fill leading 0x00 bytes and get the rest from the source.
        converge_binary.extend(repeat(0x00, converge_zero_bytes_count))
        converge_binary.extend(islice(source_iterator, HASH_BYTE_LENGTH - converge_zero_bytes_count))

        # Get the number of hashes.
        hashes_length = next(source_iterator)

        hashes = list[bytearray]()

        # Get the hashes.
        for i in range(0, hashes_length):
            hashes.append(bytearray(islice(source_iterator, HASH_BYTE_LENGTH)))

        return SMTProof(hash_to_int(converge_binary), hashes)
