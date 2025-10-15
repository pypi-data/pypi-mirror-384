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

from abc import ABC, abstractmethod
from collections.abc import Callable

from .node import LeafNode, Node, ParentNode
from .smt_proof import SMTProof
from .utility import BITS, HASH_BIT_LENGTH, NULL_HASH, OUTER_BIT, block_hash, validate_hash


class _FinalizeStepResult(ABC):
    """
    Finalize step result.
    """

    def __init__(self, hash: bytes):
        """
        Constructor.

        :param hash:
        Node hash.
        """

        self._hash = hash

    @property
    def hash(self) -> bytes:
        return self._hash

    @abstractmethod
    def save_proofs(self, hashes: list[bytes]) -> None:
        pass


class _ParentFinalizeStepResult(_FinalizeStepResult):
    """
    Finalize step result for parent node.
    """

    def __init__(self, hash: bytes, left_result: _FinalizeStepResult, right_result: _FinalizeStepResult):
        """
        Constructor.
        
        :param hash:
        Node hash.
        
        :param left_result:
        Finalize result for left node.
        
        :param right_result:
        Finalize result for right node. 
        """
        
        super().__init__(hash)
        
        self._left_result = left_result
        self._right_result = right_result

    def save_proofs(self, hashes: list[bytes]) -> None:
        # Hashes array diverges at parent node.
        left_hashes = hashes
        right_hashes = hashes.copy()
        
        # Proofs have opposite side hashes and are constructed so that first entry is the lowest peer hash.
        left_hashes.insert(0, self._right_result.hash)
        right_hashes.insert(0, self._left_result.hash)
        
        self._left_result.save_proofs(left_hashes)
        self._right_result.save_proofs(right_hashes)


class _LeafFinalizeStepResult(_FinalizeStepResult):
    """
    Finalize step result for leaf node.
    """

    def __init__(self, hash: bytes, proofs_dict: dict[int, SMTProof], index: int, converge: int):
        """
        Constructor.
        
        :param hash:
        Node hash.
        
        :param proofs_dict:
        Proofs dictionary. 
        
        :param index:
        Node index.
        
        :param converge:
        Bitmap of converged nodes.
        """

        super().__init__(hash)

        self._proofs_dict = proofs_dict
        self._index = index
        self._converge = converge

    def save_proofs(self, hashes: list[bytes]) -> None:
        self._proofs_dict[self._index] = SMTProof(self._converge, hashes)


class OptimizedSMT:
    """
    Optimized sparse Merkle tree.
    """

    def __init__(self, allow_non_inclusion: bool):
        """
        Constructor.

        :param allow_non_inclusion:
        If true, non-inclusion is allowed and nodes without hashes are set to ~NULL_HASH~.
        """

        self._allow_non_inclusion = allow_non_inclusion
        """
        If true, non-inclusion is allowed and nodes without hashes are set to NULL_HASH.
        """

        self._root: Node | None = None
        """
        Root node.
        """

        self._root_hash: bytes | None = None
        """
        Root hash.
        """

        self._proofs_dict = dict[int, SMTProof]()
        """
        Proofs dictionary.
        """

    @property
    def allow_non_inclusion(self) -> bool:
        """
        Determine if non-inclusion is allowed.
        """

        return self._allow_non_inclusion

    @property
    def root_hash(self) -> bytes:
        """
        Get the root hash.
        """

        if self._root_hash is None:
            raise ValueError("SMT not finalized")

        return self._root_hash

    def __check_not_finalized(self) -> None:
        """
        Check that the SMT has not been finalized.
        """

        if self._root_hash is not None:
            raise ValueError("SMT finalized")

    def __replace_root(self, value: Node) -> None:
        """
        Replace the root.
        """

        self._root = value

    def add(self, indexes: list[int]) -> None:
        """
        Add indexes to tree.

        :param indexes:
        Indexes of leaf nodes.
        """

        self.__check_not_finalized()

        for index in indexes:
            if index < 0 or index >= OUTER_BIT:
                raise ValueError("Invalid index")

            leaf = LeafNode(index, HASH_BIT_LENGTH)

            if self._root is None:
                self._root = leaf
            else:
                # Moving a node requires replacing it within its container.
                replace_node: Callable[[Node], None] = self.__replace_root

                node = self._root

                common_index = 0
                common_depth = 0

                done = False

                while not done:
                    bit = BITS[common_depth]
                    index_bit = index & bit
                    is_left = index_bit == 0

                    # Nodes must diverge when common depth is hit.
                    if common_depth == node.depth:
                        if isinstance(node, ParentNode):
                            parent = node

                            # Move left or right and continue.
                            if is_left:
                                node = node.left

                                replace_node = parent.replace_left
                            else:
                                node = node.right

                                replace_node = parent.replace_right
                        else:
                            # Having common depth with a leaf node means that index is duplicated.
                            raise ValueError("Duplicate index")
                    elif node.index & bit == index_bit:
                        # Current bits match so keep going.
                        common_index |= index_bit
                        common_depth += 1
                    else:
                        # Create new parent for current node and new leaf and replace.
                        replace_node(ParentNode(common_index, common_depth, leaf if is_left else node, node if is_left else leaf))

                        done = True

    def set_hash(self, index: int, hash: bytes) -> None:
        """
        Set the hash of a node.

        :param index:
        Index.

        :param hash:
        Hash.
        """

        self.__check_not_finalized()

        validate_hash(hash)

        node = self._root

        if node is None:
            raise ValueError("Empty SMT")

        while isinstance(node, ParentNode):
            node = node.left if index & BITS[node.depth] == 0 else node.right

        # Leaf node will always be found but may not be a match as only a subset of bits is used to get here.
        if node.index != index:
            raise ValueError("Index not found")

        node.hash = hash

    @staticmethod
    def __pad_hash(hash: bytes, node_index: int, node_depth: int, depth: int) -> bytes:
        """
        Pad a hash and rehash to preserve path to the root.

        :param hash:
        Hash.

        :param node_index:
        Node index.

        :param node_depth:
        Node depth.

        :param depth:
        Current depth.

        :return:
        Input hash if depths are equal or hash of padded input hash if not.
        """

        if node_depth != depth:
            left_pad: list[int] = []
            right_pad: list[int] = []

            # Hash is padded on the left or right with the byte value of the depth to preserve path to the root.
            for i in range(node_depth - 1, depth - 1, -1):
                if node_index & BITS[i] == 0:
                    right_pad.append(i)
                else:
                    left_pad.insert(0, i)

            # Pad and rehash.
            hash_pad = block_hash(bytes(left_pad), hash, bytes(right_pad))
        else:
            # No padding and therefore no rehashing required.
            hash_pad = hash

        return hash_pad

    def __finalize_step(self, node: Node, parent_converge: int, depth: int) -> _FinalizeStepResult:
        """
        Perform the next step in finalizing a node.

        :param node:
        Node.

        :param parent_converge:
        Bitmap of parent converged nodes.

        :param depth:
        Current depth.

        :return:
        Finalize step result.
        """

        result: _FinalizeStepResult

        # Bitmap of converged nodes is the parent's plus the bit representing the current height (inverse of depth).
        converge = parent_converge | BITS[HASH_BIT_LENGTH - depth]

        if isinstance(node, ParentNode):
            child_depth = node.depth + 1

            # Finalize children.
            left_result = self.__finalize_step(node.left, converge, child_depth)
            right_result = self.__finalize_step(node.right, converge, child_depth)

            hash = block_hash(left_result.hash, right_result.hash)

            result = _ParentFinalizeStepResult(OptimizedSMT.__pad_hash(hash, node.index, node.depth, depth), left_result, right_result)
        else:
            if node.hash is None:
                if not self._allow_non_inclusion:
                    raise ValueError("Hash missing")
                
                node.hash = NULL_HASH
                
            result = _LeafFinalizeStepResult(OptimizedSMT.__pad_hash(node.hash, node.index, node.depth, depth), self._proofs_dict, node.index, converge)

        return result

    def finalize(self) -> None:
        """
        Finalize the SMT by calculating the hash of all the parent nodes and building the proofs.
        """

        root = self._root

        if root is not None:
            result = self.__finalize_step(root, 0, 0)

            self._root_hash = result.hash

            result.save_proofs([])
        else:
            self._root_hash = NULL_HASH

    def proof(self, index) -> SMTProof:
        """
        Get a proof.

        :param index:
        Index.
        """

        proof = self._proofs_dict.get(index)

        if proof is None:
            raise ValueError("Proof not found")

        return proof

    def __reset_node(self, node: Node) -> None:
        """
        Reset an individual node and its children.

        :param node:
        Node.
        """

        if isinstance(node, ParentNode):
            self.__reset_node(node.left)
            self.__reset_node(node.right)
        else:
            node.hash = None

    def reset(self) -> None:
        """
        Reset the SMT.
        """

        root = self._root

        if root is not None:
            root.reset()

        self._root_hash = None
        self._proofs_dict.clear()
