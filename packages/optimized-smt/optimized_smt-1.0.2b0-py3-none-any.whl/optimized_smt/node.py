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

from abc import ABC, abstractmethod


class _BaseNode(ABC):
    """
    Base node.
    """

    def __init__(self, index: int, depth: int):
        """
        Constructor.

        :param index:
        Index.

        :param depth:
        Depth at which node exists in fully-realized SMT.
        """

        self._index = index
        self._depth = depth

    @property
    def index(self) -> int:
        """
        Get the index.
        """

        return self._index

    @property
    def depth(self) -> int:
        """
        Get the depth.
        """

        return self._depth
    
    @abstractmethod
    def reset(self) -> None:
        """
        Reset the node.
        """

        pass


class ParentNode(_BaseNode):
    """
    Parent node containing left and right child nodes.
    """

    def __init__(self, index: int, depth: int, left: Node, right: Node):
        """
        Constructor.

        :param index:
        Index.

        :param depth:
        Depth at which node exists in fully-realized SMT.

        :param left:
        Left node.

        :param right:
        Right node.
        """

        super().__init__(index, depth)

        self._left = left
        self._right = right

    @property
    def left(self) -> Node:
        """
        Get the left node.
        """

        return self._left

    def replace_left(self, value: Node) -> None:
        """
        Replace the left node.
        """

        self._left = value

    @property
    def right(self) -> Node:
        """
        Get the right node.
        """

        return self._right

    def replace_right(self, value: Node) -> None:
        """
        Replace the right node.
        """

        self._right = value
        
    def reset(self) -> None:
        self._left.reset()
        self._right.reset()


class LeafNode(_BaseNode):
    """
    Leaf node.
    """

    def __init__(self, index: int, depth: int):
        """
        Constructor.

        :param index:
        Index.

        :param depth:
        Depth at which node exists in fully-realized SMT.
        """

        super().__init__(index, depth)

        self._hash: bytes | None = None
        
    @property
    def hash(self) -> bytes | None:
        """
        Get the hash.
        """
        
        return self._hash

    @hash.setter
    def hash(self, value: bytes):
        """
        Set the hash.
        """

        if self._hash is not None:
            raise ValueError("Hash already set")
        
        self._hash = value

    def reset(self) -> None:
        self._hash = None


type Node = ParentNode | LeafNode
"""
Node. Union type ensures that isinstance test is binary.
"""
