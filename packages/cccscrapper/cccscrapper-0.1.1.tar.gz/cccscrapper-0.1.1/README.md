# pyscrapper

A simple Python package for crawling and structure validation.  

- `get_structure.py`
- `validate_get_structure.py`
- `crawl.py`
- `validate_crawl.py`

## Installation

```bash
pip install -e .

get_structure.py --out output/topic_structure.json
init(config, url)
 
validate_get_structure.py --out output/topic_structure.json
init()
 
crawl.py --url https://topic.com --out output
init(config)
 
validate_crawl.py --out output
init()

