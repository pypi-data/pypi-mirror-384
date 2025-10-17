# GCSizeMatchedControls  

### GCSizeMatchedControls can randomly select size and GC-content matched genomic regions.  

the input file is bed file.  
the output file is bed file.  
#### usage:
``` 
    GCSizeMatchedControls \
    -i "input.bed" \
    -f "mm10.fasta" \
    -s 123 \
    -t 100 \
    -o "output.bed"
```

### Installation 
#### requirement for installation  
python>=3.12  
numpy  
pandas  
argparse  
pysam  
pybedtools  

#### pip install GCSizeMatchedControls==1.0.3
https://pypi.org/project/GCSizeMatchedControls/1.0.3/

