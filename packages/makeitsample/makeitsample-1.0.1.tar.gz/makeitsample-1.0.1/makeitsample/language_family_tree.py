import networkx as nx
import pandas as pd
import json
import random
import io


def max_depth(tree, root=None):
        """
        Calculate the maximum depth of the tree.
        
        Parameters:
            tree (nx.DiGraph): The tree structure.
            root (str): The root node of the tree.
        
        Returns:
            int: The maximum depth of the tree.
        """
        if root is None:
            root = str(next(iter(nx.topological_sort(tree))))
        depths = nx.single_source_shortest_path_length(tree, root)
        return max(depths.values())
    

def add_pseudonodes(tree):
        """
        Add nodes to the tree in order to project the leaves to the bottom
        level of the tree.
        """
        tree_depth = max_depth(tree)
        pseudo_count = 0
        languages = [node for node in tree.nodes if tree.nodes[node]["type"] == "language"]
        for node in languages:
            current = node
            if tree.nodes[node]["type"] == "language":
                # get the distance from the current node to the root
                node_depth = 0
                parent = list(tree.predecessors(node))
                while parent:
                    node_depth += 1
                    parent = list(tree.predecessors(parent[0]))
                while node_depth < tree_depth:
                    # add a pseudo node
                    pseudo_count += 1
                    pseudo_node = f"{node}_pseudo_{pseudo_count}"
                    tree.add_node(pseudo_node, name=pseudo_node, type="pseudo")
                    tree.add_edge(current, pseudo_node)
                    current = pseudo_node
                    node_depth += 1
        return tree


class LanguageFamilyTree(nx.DiGraph):
    def __init__(self, filepath=None, fileobj=None):
        """
        Initialize the LanguageFamilyTree with a CSV file path.
        
        Parameters:
            filepath (str): The path to the CSV file containing the data.
        """
        super().__init__()
        if filepath:
            self.load_and_build_tree(filepath=filepath)
        elif fileobj:
            self.load_and_build_tree(fileobj=fileobj)

    def load_tree_data(self, filepath=None, fileobj=None) -> pd.DataFrame:
        """
        Load the CSV file into a DataFrame.
        
        Returns:
            pd.DataFrame: The loaded data.
        """
        if filepath:
            return pd.read_csv(filepath)
        elif fileobj:
            return self.load_tree_from_file_object(fileobj)
        else:
            raise ValueError("Either filepath or fileobj must be provided.")
    
    def load_tree_from_file_object(self, fileobj) -> pd.DataFrame:
        """
        Load the CSV file from a file object (already open) into a DataFrame.
        
        Returns:
            pd.DataFrame: The loaded data.
        """
        
        tetx_file = io.TextIOWrapper(fileobj, encoding='utf-8')
        return pd.read_csv(tetx_file)

    def make_tree(self, df: pd.DataFrame):
        """
        Create a tree structure from a DataFrame.
        
        Parameters:
            df (pd.DataFrame): A DataFrame containing the tree structure.
        """
        required_columns = {"id", "name", "parent_id", "type"}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")
        
        if not df['type'].isin(['language', 'group', 'family']).all():
            raise ValueError("Column 'type' must contain only 'language', 'group' or 'family'")
        
        # Check if the column 'type' contains exactly one value "family"
        if (df['type'] == "family").sum() != 1:
            raise ValueError("The column 'type' must contain exactly one value 'family'.")
        
        for _, row in df.iterrows():
            node_attributes = row.drop(labels=['id', 'name', 'parent_id', 'type']).to_dict()
            self.add_node(row['id'], name=row['name'], type=row['type'], **node_attributes)
            # TODO: Add the possibility to import bib entries from GlottoLog
        
        for _, row in df.iterrows():
            if not pd.isna(row['parent_id']):
                self.add_edge(row['parent_id'], row['id'])
        
        if not self.tree_check():
            raise ValueError("The graph is not a valid tree.")

    def tree_check(self) -> bool:
        """
        Checks if the given directed graph is a tree.
        
        Returns:
            bool: True if the graph is a tree, False otherwise.
        """
        if not nx.is_tree(self):
            if not nx.is_weakly_connected(self):
                components = list(nx.weakly_connected_components(self))
                raise ValueError(f"The graph is not weakly connected. It has multiple components.\n"
                                 f"Components: {components}")
            try:
                cycle = nx.find_cycle(self)
                raise ValueError(f"The graph is not a tree. It has a cycle: {cycle}")
            except nx.exception.NetworkXNoCycle:
                pass
            if self.number_of_edges() != self.number_of_nodes() - 1:
                raise ValueError("The graph is not a tree. The number of edges must be one less than the number of nodes.")
            return False
        return True

    def add_pseudogroups(self):
        """
        Add pseudogroups to the tree.
        """
        def group_siblings(node) -> bool:
            ancestors = list(self.predecessors(node))
            try:
                parent = ancestors[0]
                siblings = list(self.successors(parent))
                siblings.remove(node)
                for s in siblings:
                    if self.nodes[s]["type"] == "group":
                        return True
            except IndexError:
                return False
            return False
        
        languages = [node for node in self.nodes if self.nodes[node]["type"] == "language"]
        for lang in languages:
            if group_siblings(lang):
                self.add_node(f"{lang}_group", name=f"{lang}_group", type="group")
                parent = list(self.predecessors(lang))[0]
                self.remove_edge(parent, lang)
                self.add_edge(parent, f"{lang}_group")
                self.add_edge(f"{lang}_group", lang)
        
    def load_and_build_tree(self, filepath=None, fileobj=None):
        """
        Load the data and build the tree.
        """
        if filepath is None and fileobj is None:
            raise ValueError("Either filepath or fileobj must be provided.")
        if fileobj:
            df = self.load_tree_from_file_object(fileobj=fileobj)
        else:
            df = self.load_tree_data(filepath=filepath)
        self.make_tree(df)
        self.add_pseudogroups()
        
    def to_dict(self, node=None):
        """Convert a node and its children to a dictionary recursively."""
        
        # If no node is provided, start from the root node
        if node is None:
            node = next(iter(nx.topological_sort(self)))
        
        # Get the attributes of the current node
        node_data = self.nodes[node]
        
        # Build the dictionary for this node
        node_dict = {
            "id": node,
            "attributes": {k: v for k, v in node_data.items() if pd.notna(v)},
            "children": [self.to_dict(child) for child in self.successors(node)]
        }
        if not node_dict["children"]:
            del node_dict["children"]
        return node_dict
    
    def export_tree(self, filepath: str, format="csv"):

        def export_csv(self, filepath):    
            """
            Export the tree to a CSV file.
            
            Parameters:
                filepath (str): The path to the output CSV file.
            """
            data = []
            for node in self.nodes(data=True):
                node_id, attributes = node
                if attributes.get("type") != "pseudo":
                    parent_id = next(iter(self.predecessors(node_id)), None)
                    data.append({**{"id": node_id, "parent_id": parent_id}, **attributes})
            
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False)
            print(f"Tree exported to {filepath}")
        
        def export_json(self, filepath):
            """
            Export the tree to a JSON file.
            
            Parameters:
                filepath (str): The path to the output JSON file.
            """
            
            # Convert the tree starting from the root node
            tree_dict = self.to_dict()
                        
            # Write the tree dictionary to a JSON file
            with open(filepath, "w") as json_file:
                json.dump(tree_dict, json_file, indent=4)
            print(f"Tree exported to {filepath}")
        
        if format == "csv":
            export_csv(self, filepath)
        elif format == "json":
            export_json(self, filepath)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
    def get_subtrees(self, node):
        """
        Get all subtrees of a given node.
        
        Parameters:
            node (str): The node to get subtrees for.
        
        Returns:
            dict: A dictionary where keys are child nodes and values are the corresponding subtrees.
        """
        if not self.has_node(node):
            raise ValueError(f"Node {node} does not exist in the tree.")
        
        subtrees = {}
        children = list(self.successors(node))

        for child in children:
            # get the descendants of the node
            descendants = nx.descendants(self, child)
            descendants.add(child) # add the root of the subtree

            # extract the subtree as a new DiGraph
            subtree = self.subgraph(descendants).copy()
            subtrees[child] = subtree

        return subtrees
    
    def compute_dv(self, node, max_depth_value):
        """
        Compute the diversity value for a given node.
        
        Parameters:
            node (str): The node to compute the diversity value for.
            max_depth_value (int): The maximum depth of any family tree parallel to the one rooted at the given node.
            
        Returns:
            float: The diversity value for the node.
        """
        
        def level_contribution(self, node, max_depth_value):
            """
            Compute the contribution of a node at a given level.
            
            Parameters:
                node (str): The node to compute the contribution for.
                max_depth_value (int): The maximum depth of the tree.
                
            Returns:
                float: The contribution of the node at the given level.
            """
            # Perform BFS from the given node
            tree = self.copy()
            tree = add_pseudonodes(tree)
            levels = {node: 0}
            queue = [node]
            for current in queue:
                for child in tree.successors(current):
                    if child not in levels:
                        levels[child] = levels[current] + 1
                        queue.append(child)
                        
            # Calculate the number of nodes at each level
            max_level = max(levels.values())
            level_counts = [0] * (max_level + 1)
            for level in levels.values():
                level_counts[level] += 1
                
            contributions = []
            for k in range(len(level_counts)):
                if k == 0:
                    ck = 0
                else:
                    nk = level_counts[k]
                    nk_1 = level_counts[k - 1]
                    ck = contributions[-1] + (nk - nk_1) * (max_depth_value - (k - 1)) / max_depth_value
                contributions.append(ck)
                
            return contributions[1:]
        
        if self.nodes[node]["type"] in ["language", "pseudo"]:
            return None
        if self.nodes[node]["type"] in ["group", "family"]:
            if self.capacity(node) == 0:
                return 0
            if self.capacity(node) == 1:
                return 1
        contributions = level_contribution(self, node, max_depth_value)
        # Compute the average contribution
        # to get the diversity value
        # DV is the mean of contributions
        return sum(contributions) / len(contributions)
    
    def update_tree_dv(self, root=None, max_depth_value=None):
        """
        Update the tree with diversity values for each node.
        
        Parameters:
            root (str): The root node of the tree.
            max_depth (int): The maximum depth of any tree.
        """
        
        if max_depth_value is None:
            max_depth_value = max_depth(self)
            
        # get the root node
        if root is None:
            root = next(iter(nx.topological_sort(self)))
        
        # calculate the dv for the root node
        dv = self.compute_dv(root, max_depth_value)
        
        # update the root node with the dv
        if dv is not None:
            self.nodes[root]["dv"] = dv
        
        # generate subtrees for each child of the root node
        subtrees = self.get_subtrees(root)
        
        max_depth_value = max([max_depth(subtree, child) for child, subtree in subtrees.items()], default=0)
        
        # calculate the dv for each child node
        for child in subtrees:
            self.update_tree_dv(child, max_depth_value)
    
    def capacity(self, node=None) -> int:
        """
        Calculate the capacity of a node in the language family tree.
        The capacity is defined as the number of descendands nodes of type
        "language" of the node.

        Args:
            node: The node for which to calculate the capacity (default is the root node).

        Returns:
            int: The capacity of the node.
        """
        
        if node is None:
            node = next(iter(nx.topological_sort(self)))
                
        # if the node itself is a language, return 0 (it has no capacity)
        if self.nodes[node]["type"] == "language":
            return 0
        
        # get the descendants of type "language" of the node
        languages = [l for l in nx.descendants(self, node) if self.nodes[l]["type"] == "language"]
        
        return len(languages)
    
    def distribute_sample(self, node=None, n=10):
        """
        Distribute a given number (n) of languages across the tree.
        
        Parameters:
            node (str): The node to distribute languages from (default is the root node).
            n (int): The number of languages to distribute.
        """
        
        def distribute_successors(self, node, n):
            """
            Distribute a given number of units (n) among the successors of a node in a directed graph.
            
            Parameters:
                node (str): The node to distribute units from.
                n (int): The number of units to distribute.
            
            Returns:
                dict: A dictionary where keys are successor nodes and values are the number of units assigned to each.
            """
            # If the node is of type "language", distribution does not apply
            if self.nodes[node]["type"] == "language":
                return None
            
            # get the successors of the node
            successors = list(self.successors(node))
            
            if all(self.nodes[s]["type"] == "language" for s in successors) and self.nodes[node]["type"] == "family":
                available_langs = [s for s in successors if self.nodes[s]["type"] == "language"]
                sample_size = min(len(available_langs), n)
                for selected_lang in random.sample(available_langs, sample_size):
                    self.nodes[selected_lang]["selected"] = True
                # We handled this node completely — no further recursion
                self.nodes[node].pop("n", None)  # remove n so it won't be used again
                return None
            
            if any(self.nodes[s]["type"] == "language" for s in successors):
                return None
                    
            # Calculate the capacity of each successor
            capacities = {s: self.capacity(s) for s in successors}
            
            # Check if there is enough capacity to distribute n units
            if sum(capacities.values()) < n:
                raise ValueError("Not enough capacity to distribute the languages.")
            
            # initialize the distribution dictionary
            if n >= len(successors):
                distribution = {}
                for s in successors:
                    if capacities[s] > 0:
                        distribution[s] = 1
                        n -= 1
            else:
                distribution = {s: 0 for s in successors}
            
            # calculate the probabilities based on the dv
            probabilities = {s: self.nodes[s]["dv"] for s in successors}

            # distribute the remaining units based on the capacities and probabilities
            while n > 0:
                for s in successors:
                    # if a successor reaches its capacity, set its probability to 0
                    if distribution[s] == capacities[s]:
                        probabilities[s] = 0
                
                # select a successor based on the probability
                selected_element = random.choices(list(distribution.keys()), weights=list(probabilities.values()), k=1)[0]
                
                # add  unit to the selected successor
                distribution[selected_element] += 1
                n -= 1
            return distribution
        
        def select_languages(self):
            """
            Select the languages to be included in the sample after the distribution.
            """
            for node_id, node_data in self.nodes(data=True):
                if node_data.get("type") in ["group", "family"]:
                    if "n" in node_data:
                        languages = list(self.successors(node_id))
                        sample_size = min(len(languages), node_data["n"])
                        for selected_lang in random.sample(languages, sample_size):
                            self.nodes[selected_lang]["selected"] = True

                        del self.nodes[node_id]["n"]
        
        # if the node is None, set it to the root node
        if node is None:
            node = next(iter(nx.topological_sort(self)))
        
        # get the distribution for the node
        distribution = distribute_successors(self, node, n)
        
        # if the distibution is empty, assign n to the node and return None
        if distribution is None:
            node_capacity = self.capacity(node)
            if n > node_capacity:
                n = node_capacity
            self.nodes[node]["n"] = n
            return None
        
        # delete n from the node
        if "n" in self.nodes[node]:
            del self.nodes[node]["n"]
            
        # recursively distribute the languages to the successors
        for s in distribution:
            self.nodes[s]["n"] = distribution[s]
            self.distribute_sample(s, distribution[s])
        
        # select the languages to be included in the sample
        select_languages(self)
    
    def export_sample(self, type="csv", filepath="sample.csv"):
        """
        Export the sample of languages selected from the tree.
        Parameters:
            type (str): The type of export (default is "csv").
        """
        def export_csv(tree, filepath):
            """
            Export the sample to a CSV file.
            
            Parameters:
                filepath (str): The path to the output CSV file.
            """
            data = []
            for node_id, attributes in tree.nodes(data=True):
                if attributes.get("selected"):
                    data.append({**{"id": node_id}, **attributes})
            
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False)
            print(f"Sample exported to {filepath}")
        
        if type == "csv":
            export_csv(self, filepath)
        else:
            raise ValueError(f"Unsupported export type: {type}")
    
    def keep_selected(self):
        """
        Keep only the selected languages with their groups in the tree.
        """
        sample_tree = self.copy()
        selected_languages = [node for node, data in sample_tree.nodes(data=True) if data.get("selected")]
        selected_groups = set()
        
        for lang in selected_languages:
            # get the path from the language to the root
            group = list(nx.ancestors(sample_tree, lang))
            for elem in group:
                selected_groups.add(elem)
                
        # keep only the selected languages and their groups
        nodes_to_keep = selected_languages + list(selected_groups)
        nodes_to_remove = [node for node in sample_tree.nodes if node not in nodes_to_keep]
                
        # remove the edges to the removed nodes
        for node in nodes_to_remove:
            predecessors = list(sample_tree.predecessors(node))
            for pred in predecessors:
                sample_tree.remove_edge(pred, node)
            successors = list(sample_tree.successors(node))
            for succ in successors:
                sample_tree.remove_edge(node, succ)
        
        # remove the nodes from the tree
        sample_tree.remove_nodes_from(nodes_to_remove)
        
        return sample_tree