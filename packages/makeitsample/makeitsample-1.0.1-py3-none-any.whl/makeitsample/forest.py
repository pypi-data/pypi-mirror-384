import os
import networkx as nx
if __name__ in ["forest", "__main__"]:
    from language_family_tree import *
else:
    from .language_family_tree import *
import random
import json
import pandas as pd


class Forest(list):
    """
    A class representing a collection of LanguageFamilyTree objects.
    
    Inherits from list to allow for easy manipulation of multiple trees.
    """
    
    def __init__(self, *args, dir=None):
        """
        Initialize the Forest with multiple LanguageFamilyTree objects.
        
        Parameters:
            *args: Variable length argument list of LanguageFamilyTree objects.
            dir (str): Directory to import trees from.
            dv (bool): Whether to compute diversity values for the trees.
        """
        super().__init__()
        
        if dir:
            self.import_forest(dir)
        
        for arg in args:
            if isinstance(arg, LanguageFamilyTree):
                self.append(arg)
            else:
                raise ValueError("Only LanguageFamilyTree objects can be added to the forest.")
    
    def append(self, tree):
        """
        Append a new LanguageFamilyTree to the forest.
        
        Parameters:
            tree (LanguageFamilyTree): The tree to append.
        """
        if isinstance(tree, LanguageFamilyTree):
            super().append(tree)
        else:
            raise ValueError("Only LanguageFamilyTree objects can be added to the forest.")
    
    def import_forest(self, dir: str):
        """
        Import multiple trees from a directory.
        
        Parameters:
            dir (str): The directory containing the tree files.
        """        
        for filename in os.listdir(dir):
            if filename.endswith(".csv"):
                filepath = os.path.join(dir, filename)
                tree = LanguageFamilyTree(filepath)
                self.append(tree)
    
    def export_forest(self, dir: str, format="csv"):
        """
        Export the forest to a CSV or JSON file.
        
        Parameters:
            dir (str): The directory where to store the output files.
            format (str): The format of the output file. Can be 'csv' or 'json'.
        """
        if not os.path.exists(dir):
            os.makedirs(dir)
        if not isinstance(dir, str):
            raise ValueError("The directory must be a string.")
        if not os.path.isdir(dir):
            raise ValueError(f"{dir} is not a directory.")
        
        if format == "csv":
            for i, tree in enumerate(self):
                root = next(iter(nx.topological_sort(tree)))
                tree.export_tree(f"{dir}/{root}.csv", format="csv")
        elif format == "json":
            for i, tree in enumerate(self):
                root = next(iter(nx.topological_sort(tree)))
                tree.export_tree(f"{dir}/{root}.json", format="json")
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def dv(self):
        """
        Update the trees in the forest with diversity values.
        """
        if not self:
            raise ValueError("The forest is empty.")

        max_depth_value = max([max_depth(tree) for tree in self])
        
        for tree in self:
            tree.update_tree_dv(max_depth_value=max_depth_value)
    
    def distribute_sample_families(self, n: int):
        """
        Distribute a given number (n) of languages across the trees in the
        forest.
        
        Parameters:
            n (int): The number of languages to distribute.
            
        Returns:
            dict: A dictionary where keys are tree indices and values are
            lists of languages.
        """
        if n <= 0:
            raise ValueError("The number of languages to distribute must be positive.")
        if not self:
            raise ValueError("The forest is empty.")
        
        # get the capacities of each tree
        capacities = {self.index(tree): tree.capacity() for tree in self}
        
        if sum(capacities.values()) < n:
            raise ValueError("Not enough capacity in the forest to distribute the languages.")
        
        n_left = n
        if n_left >= len(self):
            # distribute one language to each tree
            distribution = {self.index(tree): 1 for tree in self if tree.capacity() > 0}
            n_left -= len(distribution)
        else:
            distribution = {self.index(tree): 0 for tree in self}
        
        # calculate the dv of each tree
        self.dv()
        
        # get all dvs and store them as probabilities
        probabilities = []
        for tree in self:
            root = next(iter(nx.topological_sort(tree)))
            probabilities.append(tree.nodes[root]["dv"])
        
        while n_left > 0:
            # distribute the remaining languages according to their dv and capacities
            for tree in self:
                # if a family reaches its capacity, set its probability to 0
                if distribution[self.index(tree)] == capacities[self.index(tree)]:
                    probabilities[self.index(tree)] = 0
            
            # select a family based on the probability
            selected_element = random.choices(list(distribution.keys()), weights=probabilities, k=1)[0]
            
            # add a unit to the selected family
            distribution[selected_element] += 1
            n_left -= 1 # decrease the remaining units
        
        return distribution
    
    def make_sample(self, n: int):
        """
        Sample a given number (n) of languages from the trees in the forest.
        
        Parameters:
            n (int): The number of languages to sample.
        """
        # get the distribution of languages for each family
        distribution = self.distribute_sample_families(n)
        
        for index in distribution:
            self[index].distribute_sample(n=distribution[index])
        
    def export_sample(self, dir=None, format="csv", filename="sample"):
        """
        Export the sampled languages to a CSV or JSON file.
        
        Parameters:
            dir (str): The directory where to store the output files.
            format (str): The format of the output file. Can be 'csv' or 'json'.
        """
        if dir is None:
            dir = "sample"
                    
        if not os.path.exists(dir):
            os.makedirs(dir)
        
        if format == "csv":
            records = []
            for i, tree in enumerate(self):
                root = next(iter(nx.topological_sort(tree)))
                sampled_languages = [(node, data) for node, data in tree.nodes(data=True) if data.get("selected") is True]
                for node, data in sampled_languages:
                    records.append({"id": node, **data, "family": root})
            df = pd.DataFrame(records)
            df.to_csv(f"{dir}/{filename}.csv", index=False)                
        elif format == "json":
            data = []
            for i, tree in enumerate(self):
                sampled_tree = tree.keep_selected()
                dict_tree = sampled_tree.to_dict()
                data.append(dict_tree)
            with open(f"{dir}/{filename}.json", "w") as f:
                json.dump(data, f, indent=4)
        else:
            raise ValueError(f"Unsupported export format: {format}")
