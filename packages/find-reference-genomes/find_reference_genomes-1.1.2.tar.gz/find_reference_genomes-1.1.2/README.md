# find_reference_genomes

Easily find and download reference genomes stored at NCBI

# Dependencies
- [NCBI datasets](https://github.com/ncbi/datasets) 
- Python >= 3.7

```
find_reference_genomes -h
usage: find_reference_genomes [-h] [-n NAME] [-d DOWNLOAD] [-p] [--no-genome] [-o OUTPUT_DIR] [-l {chromosome,complete,scaffold,contig}]
                              [--max-rank {strain,subspecies,species,genus,subfamily,family,suborder,order,subclass,class,phylum,kingdom,superkingdom}] [--allow-clade]

Find and download reference genomes from the NCBI

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Scientific name of the species of interest
  -d DOWNLOAD, --download DOWNLOAD
                        Comma-separated list of GCA accessions to download (example: '-d GCA_047652355.1,GCA_049901935.1,GCA_048126915.1')
  -p, --proteins        When used with --download, also download the corresponding protein FASTA files (.faa)
  --no-genome           When used with --download, do not download the genome (use with -p to download only proteins)
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        If using --download, path to the output directory to store the downloaded genomes
  -l {chromosome,complete,scaffold,contig}, --level {chromosome,complete,scaffold,contig}
                        Limits the results to at least this level of assembly
  --max-rank {strain,subspecies,species,genus,subfamily,family,suborder,order,subclass,class,phylum,kingdom,superkingdom}
                        Limits the search to taxonomic ranks up to the specified level (e.g., '--max-rank genus' will only search up to genus level)
  --allow-clade         Allow the search to include clade level (default: False)
```
