# /usr/bin/python3
"""Script to specify arguments on CLI"""
import os
import click
import polars as pl
import pyBigWig as bw

from readfiles import readbam
from fileprocessor import dftobed, bedtobigwig
from getcandidates import gettranscripts, preporfs, orfrelativeposition
from filewriter import saveorfsandexons
from bigwigtodf import bigwigtodf


@click.group()
def function():
    pass


@function.command()
@click.argument("input")
@click.option(
    "--chromsize", "-c", help="Provide a file containing the chromosome sizes"
)
def cli(input, chromsize):
    """
    docstring
    """
    location = os.getcwd() + "/" + input
    # if file is provided
    if os.path.isfile(location):
        # read in bam file
        df = readbam(location)
        # calculate asite + converting to BedGraph
        beddf = dftobed(df)

        if not os.path.exists("data/file.bedGraph"):
            bedfile = beddf.write_csv("file.bedGraph", separator="\t")

            # Converting Bedgrapgh to Bigwig format
            bedtobigwig(bedfile, chromsize)

    # if folder with BAM files is provided
    elif os.path.isdir(location):
        list_dir = os.listdir(location)
        y = []
        filename = os.path.basename(location)
        for file in list_dir:
            bamcheck = file.split(".", 1)
            if bamcheck[1] == "bam":
                location = location + "/" + file
                # read in bam file
                df = readbam(location)
                # calculate asite and converting dataframe to BEDGRAPH format
                asitedf = dftobed(df)
                y.append(asitedf)
            else:
                click.echo("No .bam files found in folder")
        df_merged = pl.concat(y)
        df_merged.write_csv(f"{filename}.bedGraph", separator="\t")
        bedtobigwig(bedfile, chromsize)


@function.command()
@click.option(
    "--seq", "-s", help="Provide a file containing the genomic sequence (.fa)"
)
@click.option(
    "--tran", "-t", help="Provide a file containing the transcript sequences (.fa)"
)
@click.option("--ann", "-a", help="Provide a file containing the annotation (.gtf)")
@click.option("--starts", "-sta", default="ATG", help="Provide a list of start codons")
@click.option(
    "--stops", "-stp", default="TAA, TAG, TGA", help="Provide a list of stop codons"
)
@click.option("--minlen", "-min", default=0, help="Provide the minimum length")
@click.option("--maxlen", "-max", default=1000000, help="Provide the maximum length")
def orfprep(seq, ann, tran, starts, stops, minlen, maxlen):
    """
    docstring
    """
    if seq and ann:
        transcript = gettranscripts(seq, ann)
    elif tran:
        transcript = tran
    else:
        raise Exception(
            "Must provide genomic sequence and annotation or transcript sequences"
        )

    orfdf = preporfs(transcript, starts.split(", "), stops.split(", "), minlen, maxlen)

    orf_ann_df, exondf = orfrelativeposition(ann, orfdf)
    saveorfsandexons(orf_ann_df, exondf)


@function.command()
@click.option("--bigwig", "-bw", help="Provide a Bigwig file to convert")
@click.option("--exon", "-ex", help="Provide a file containing exon positions")
def bigwigconverter(bigwig, exon):
    """
    docstring
    """
    bwtrancoords = bigwigtodf(bigwig, exon)
    bwtrancoords.write_csv("data/files/bw_tran.csv")


if __name__ == "__main__":
    function()
