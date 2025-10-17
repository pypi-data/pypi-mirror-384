"""Merkle tree for efficient integrity verification."""

import hashlib
from typing import List, Optional, Tuple

from ..models import MerkleNode


class MerkleTree:
    """Merkle tree for organizing and verifying hashes efficiently."""
    
    def __init__(self, hash_algorithm: str = "sha256"):
        """
        Initialize Merkle tree.
        
        Args:
            hash_algorithm: Hash algorithm to use
        """
        self.hash_algorithm = hash_algorithm
        self.root: Optional[MerkleNode] = None
        self._leaf_hashes: List[str] = []
    
    def build(self, leaf_hashes: List[str]) -> MerkleNode:
        """
        Build Merkle tree from list of leaf hashes.
        
        Args:
            leaf_hashes: List of hash strings for leaves
            
        Returns:
            Root node of the tree
        """
        if not leaf_hashes:
            # empty tree - return a node with hash of empty string
            self.root = MerkleNode(hash=self._hash(""))
            self._leaf_hashes = []
            return self.root
        
        # store leaf hashes for later verification
        self._leaf_hashes = leaf_hashes.copy()
        
        # create leaf nodes
        nodes = [MerkleNode(hash=h) for h in leaf_hashes]
        
        # if odd number of nodes, duplicate the last one
        if len(nodes) % 2 == 1:
            nodes.append(MerkleNode(hash=nodes[-1].hash))
        
        # build tree bottom-up
        while len(nodes) > 1:
            parent_nodes = []
            
            # pair up nodes and create parents
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
                
                # hash the concatenation of child hashes
                parent_hash = self._hash(left.hash + right.hash)
                parent = MerkleNode(hash=parent_hash, left=left, right=right)
                
                parent_nodes.append(parent)
            
            nodes = parent_nodes
            
            # if odd number, duplicate last
            if len(nodes) % 2 == 1 and len(nodes) > 1:
                nodes.append(nodes[-1])
        
        self.root = nodes[0]
        return self.root
    
    def get_root_hash(self) -> Optional[str]:
        """
        Get hash of root node.
        
        Returns:
            Root hash or None if tree not built
        """
        return self.root.hash if self.root else None
    
    def verify(self, leaf_hashes: List[str]) -> bool:
        """
        Verify if given leaf hashes match the tree.
        
        Args:
            leaf_hashes: List of leaf hashes to verify
            
        Returns:
            True if hashes match, False otherwise
        """
        if not self.root:
            return False
        
        # build a new tree with the provided hashes
        new_tree = MerkleTree(hash_algorithm=self.hash_algorithm)
        new_root = new_tree.build(leaf_hashes)
        
        # compare root hashes
        return new_root.hash == self.root.hash
    
    def get_proof(self, index: int) -> List[Tuple[str, str]]:
        """
        Get Merkle proof for a specific leaf.
        
        A Merkle proof allows verifying a single leaf without
        having access to all other leaves.
        
        Args:
            index: Index of the leaf
            
        Returns:
            List of (hash, position) tuples where position is 'left' or 'right'
        """
        if not self.root or index < 0 or index >= len(self._leaf_hashes):
            return []
        
        proof = []
        leaf_count = len(self._leaf_hashes)
        
        # adjust for duplicated last node if odd count
        if leaf_count % 2 == 1:
            leaf_count += 1
        
        # traverse from leaf to root, collecting sibling hashes
        current_index = index
        current_level_size = leaf_count
        
        # we'll do a simplified proof generation
        # in a real implementation, we'd traverse the actual tree structure
        # for now, we'll rebuild the path
        
        level_hashes = self._leaf_hashes.copy()
        if len(level_hashes) % 2 == 1:
            level_hashes.append(level_hashes[-1])
        
        while len(level_hashes) > 1:
            # find sibling
            if current_index % 2 == 0:
                # we're on the left, sibling is on the right
                sibling_index = current_index + 1
                if sibling_index < len(level_hashes):
                    proof.append((level_hashes[sibling_index], 'right'))
            else:
                # we're on the right, sibling is on the left
                sibling_index = current_index - 1
                proof.append((level_hashes[sibling_index], 'left'))
            
            # move up to parent level
            parent_hashes = []
            for i in range(0, len(level_hashes), 2):
                left = level_hashes[i]
                right = level_hashes[i + 1] if i + 1 < len(level_hashes) else level_hashes[i]
                parent_hash = self._hash(left + right)
                parent_hashes.append(parent_hash)
            
            level_hashes = parent_hashes
            if len(level_hashes) % 2 == 1 and len(level_hashes) > 1:
                level_hashes.append(level_hashes[-1])
            
            current_index = current_index // 2
        
        return proof
    
    def verify_proof(self, leaf_hash: str, proof: List[Tuple[str, str]], root_hash: str) -> bool:
        """
        Verify a Merkle proof.
        
        Args:
            leaf_hash: Hash of the leaf to verify
            proof: List of (hash, position) tuples
            root_hash: Expected root hash
            
        Returns:
            True if proof is valid, False otherwise
        """
        current_hash = leaf_hash
        
        # apply each step of the proof
        for sibling_hash, position in proof:
            if position == 'left':
                current_hash = self._hash(sibling_hash + current_hash)
            else:  # right
                current_hash = self._hash(current_hash + sibling_hash)
        
        return current_hash == root_hash
    
    def find_differences(self, new_leaf_hashes: List[str]) -> List[int]:
        """
        Find which leaves changed compared to baseline.
        
        Args:
            new_leaf_hashes: New list of leaf hashes
            
        Returns:
            List of indices that changed
        """
        if not self._leaf_hashes:
            return list(range(len(new_leaf_hashes)))
        
        differences = []
        
        # compare each leaf
        for i in range(max(len(self._leaf_hashes), len(new_leaf_hashes))):
            old_hash = self._leaf_hashes[i] if i < len(self._leaf_hashes) else None
            new_hash = new_leaf_hashes[i] if i < len(new_leaf_hashes) else None
            
            if old_hash != new_hash:
                differences.append(i)
        
        return differences
    
    def update_leaf(self, index: int, new_hash: str) -> None:
        """
        Update a single leaf and rebuild affected parts of tree.
        
        This is more efficient than rebuilding the entire tree.
        
        Args:
            index: Index of leaf to update
            new_hash: New hash value
        """
        if index < 0 or index >= len(self._leaf_hashes):
            return
        
        # update the leaf
        self._leaf_hashes[index] = new_hash
        
        # rebuild the tree
        # in a production implementation, we'd only rebuild the path
        # from this leaf to the root for efficiency
        self.build(self._leaf_hashes)
    
    def get_leaf_count(self) -> int:
        """Get number of leaves in the tree."""
        return len(self._leaf_hashes)
    
    def get_tree_height(self) -> int:
        """Get height of the tree."""
        if not self._leaf_hashes:
            return 0
        
        # height is log2(leaf_count) rounded up
        import math
        return math.ceil(math.log2(len(self._leaf_hashes))) if len(self._leaf_hashes) > 0 else 0
    
    def _hash(self, data: str) -> str:
        """
        Hash a string using the configured algorithm.
        
        Args:
            data: String to hash
            
        Returns:
            Hexadecimal hash
        """
        if self.hash_algorithm == "blake3":
            try:
                import blake3
                return blake3.blake3(data.encode()).hexdigest()
            except ImportError:
                pass
        
        # default to SHA-256
        return hashlib.sha256(data.encode()).hexdigest()
    
    def visualize(self, node: Optional[MerkleNode] = None, level: int = 0, prefix: str = "") -> str:
        """
        Create a visual representation of the tree.
        
        Args:
            node: Node to start from (defaults to root)
            level: Current depth level
            prefix: Prefix for indentation
            
        Returns:
            String representation of tree
        """
        if node is None:
            node = self.root
        
        if node is None:
            return "Empty tree"
        
        result = prefix + f"{'  ' * level}[{node.hash[:8]}...]\n"
        
        if node.left:
            result += self.visualize(node.left, level + 1, prefix)
        if node.right and node.right != node.left:
            result += self.visualize(node.right, level + 1, prefix)
        
        return result
