--

# RDFObject (RDFObj)

**A Python library for Object-Oriented RDF data manipulation**

## Key Features
RDFObject provides a seamless bridge between Python objects and RDF data, offering:
- **OWL to Python code generation**: Automatically generate Python classes from OWL ontologies.
- **Object-Triple Store mapping**: Map Python objects directly to RDF triples.
- **CRUD operations**: Create, Read, Update, and Delete RDF data with ease.
- **Browsing API**: Explore RDF datasets using both object models and SPARQL queries.

## Purpose
This library simplifies the exploration and manipulation of large-scale RDF datasets. It functions as an ORM-like library, mapping Python objects to RDF using auto-generated SPARQL queries. The Python class model is dynamically extracted from the OWL specification, ensuring consistency and reducing manual effort.

## Tutorial
For a hands-on guide, see:
[Custom Ontology Creation and RDF Query API Generation](https://forge.inrae.fr/pegase/wspilot/-/raw/master/hackathon/rdfobj/doc/custom_onto_with_biopax.pdf?ref_type=heads&inline=false)

## Installation
Install the library via pip:
```bash
pip install rdfobj
```

### Demo Environment
To run a full demo with Jupyter and Fuseki:
```bash
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up
docker-compose exec db bash /fuseki/load_db.sh
```

## Source Repository
[GitLab INRAE Forge](https://forge.inrae.fr/pegase/rdfobject)

---