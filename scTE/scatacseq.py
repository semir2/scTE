'''

The scATAC-seq data comes as three files, P1, P2 and the barcode, and there is no UMI

You can just align P1 and P2 with your favourite aligner (we prefer STAR with these settings):

****
teopts=' --outFilterMultimapNmax 100 --winAnchorMultimapNmax 100 --outSAMmultNmax 1 --outSAMtype BAM SortedByCoordinate --twopassMode Basic --outWigType wiggle --outWigNorm RPM'
opts='--runRNGseed 42 --runThreadN 12 --readFilesCommand zcat '

genome_mm10='--genomeDir mm10_gencode_vM21_starsolo/SAindex'
genome_hg38='--genomeDir hg38_gencode_v30_starsolo/SAindex'

# p1 = read
# p2 = barcode and UMI
# Make sure you set the correct genome index;
STAR $opts $teopts $genome_hg38 --outFileNamePrefix ss.${out} --readFilesIn ${p1} ${p2}
****

This script will then reprocess the BAM file, and put the BARCODE into CR SAM tag and spoof a UMI

The UMI is generated by incrementing the sequence, so, each UMI is up to 4^14 (26 million).
I guess there remains a change of a clash, but it should be so rare as to be basically impossible.

Require pysam


See also: bin/pack_scatacseq

'''

import sys
import gzip
import argparse
import logging

try:
    import pysam
except ImportError:
    pass # fail silently

def fastq(file_handle):
    """
    Generator object to parse a FASTQ file

    """
    name = "dummy"
    while name != "":
        name = file_handle.readline().strip()
        seq = file_handle.readline().strip()
        strand = file_handle.readline().strip()
        qual = file_handle.readline().strip()

        yield {"name": name, "strand": strand, "seq": seq, "qual": qual}
    return

def library(args):
    """
    Sequence generator iterator

    """
    if not args:
        yield ""
        return
    for i in args[0]:
        for tmp in library(args[1:]):
            yield i + tmp
    return

def build_barcode_dict(barcode_filename, save_whitelist=False, gzip_file=True):
    '''
    **Purposse**
        The BAM and the FASTQ are not guaranteed to be in the same order, so I need to make a look up for
        the read ID and the barcode

    **Arguments**
        barcode_filename (Required)

        save_whitelist (Optional, default=False)
            save out the whitelist of barcodes (i.e. the ones actually observed)\

            TODO: This should be checked against the expected whitelist, and 1bp Hamming corrected

    **Returns**
        A dict mapping <readid>: <barcode>
    '''
    assert barcode_filename, 'barcode_filename is required'

    logging.info('Building Barcode lookup table')

    barcode_lookup = {}
    if gzip_file:
        oh = gzip.open(barcode_filename, 'rt')
    else:
        oh = open(barcode_filename, 'rt')

    for fq in fastq(oh):
        barcode_lookup[fq['name']] = fq['seq']

    oh.close()

    # if expected_whitelist:
    # Correct the barcodes for Hamming = 1

    if save_whitelist:
        logging.info('Saving Whitelist')
        oh = open(save_whitelist, 'w')
        for k in barcode_lookup.keys():
            oh.write('%s\n' % (k))
    oh.close()

    return barcode_lookup

def parse_bam(infile, barcode_filename, outfile):
    inbam = pysam.open(infile)
    outfile = pysam.open(outfile)
    barcodes = fastq()

    umi_iterator = library(["ACGT"] * 14)

    for idx, read in emnumerate(inbam):
        # UMI iterator
        try:
            umi = umi_iterator.__next__()
        except StopIteration:
            umi_iterator = library(["ACGT"] * 14)

        # Check the reads:

    inbam.close()
    outfile.close()

