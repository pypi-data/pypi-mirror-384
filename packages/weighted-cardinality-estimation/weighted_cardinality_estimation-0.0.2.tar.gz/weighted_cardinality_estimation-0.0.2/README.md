# weighted-cardinality-estimation

# Przykład użycia

    from weighted_cardinality_estimation import ExpSketch

    sketch = ExpSketch(400, list(range(400)))
    sketch.add("elem1", 5)
    print(sketch.estimate())

# To install in repo use

```bash
python -m pip install -e . --no-deps --no-build-isolation -vvv
pytest
```