#!/usr/bin/env python3

from makeitsample.forest import Forest
import argparse
import random


def main():
    parser = argparse.ArgumentParser(description="Sample languages from a set of family trees.")
    parser.add_argument("-n", type=int, help="Number of languages to sample.")
    parser.add_argument("-i", "--input", type=str, help="Path to the directory containing the family trees in csv format.")
    parser.add_argument("-o", "--output", type=str, help="Path to the output directory.")
    parser.add_argument("-f", "--format", type=str, choices=["csv", "json"], default="csv", help="Output format.")
    parser.add_argument("-s", "--samplename", type=str, default="sample", help="Name of the output file.")
    parser.add_argument("-r", "--random_seed", type=int, default=None, help="Random seed for reproducibility.")
    
    args = parser.parse_args()
    if args.random_seed is not None:
        random.seed(args.random_seed)
    
    # Load the family trees from the input directory
    family_trees = Forest(dir=args.input)
    # Sample languages from the family trees
    family_trees.make_sample(n=args.n)
    # Export the sampled languages to the output directory
    family_trees.export_sample(dir=args.output, format=args.format, filename=args.samplename)
    

if __name__ == "__main__":
    main()