# Dorado web tools in Streamlit

This repository contains observer web tools for the Dorado mission, including
an interactive exposure time calculator. It is built using
[Streamlit](https://streamlit.io), a framework for easily turning Python code
into interactive data-driven web apps.

## To build

$ docker build . -t dorado-streamlit

## To run

$ docker run --rm dorado-streamlit

And then navigate to http://127.0.0.1:8051/.
