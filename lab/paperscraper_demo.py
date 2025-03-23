# from paperscraper.pubmed import get_and_dump_pubmed_papers
# drug = ['suzetrigine']
# query = [drug]

# get_and_dump_pubmed_papers(query, output_filepath='drug.jsonl')


from paperscraper.pdf import save_pdf
paper_data = {'doi': " 10.1080/09546634.2025.2474495"}
save_pdf(paper_data, filepath='paper.pdf')