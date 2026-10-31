"""
4D explorer benchmark.

Hidden objects live in R^4. An explorer (a scripted baseline or an LLM agent)
may only look at them through a limited budget of probes -- 3D slices and 3D
projections -- and must then say what the object is and predict what unseen
slices will look like. Answers are scored against ground truth known by
construction.
"""
