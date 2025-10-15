# Argumentari 🗣️

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![macOS](https://img.shields.io/badge/mac%20os-000000?style=for-the-badge&logo=macos&logoColor=F0F0F0)
![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)

---

**Argumentari** is a lightweight, cross-platform Python package for constructing, serializing, manipulating, and visualizing structured argument data.  
Build argument trees, apply formal reasoning schemes, and interactively analyze debate structures.

## Features

- Define argument nodes (`premise`, `conclusion`) and build trees
- Manipulate arguments: add, move, clone, edit, prune and collapse nodes
- Visualize argument graphs interactively
- Register and use formal argumentation schemes (e.g., Authority, Causal)
- Find and replace nodes by text or scheme
- Serialize and deserialize argument trees
- Cross-platform: Linux, macOS, Windows
- Simple API for integration into your projects

---

## Usage

### Create and manipulate an argument tree

```python
from argumentari.nodes import premise, conclusion
from argumentari.tree import argumentTree
from argumentari.manipulation import (
    addNode, removeNode, replaceNode, moveSubtree,
    editNode, cloneSubtree, findNodes, pruneNode, collapseSubtree
)

root = premise("Electric cars reduce emissions.")
child1 = premise("EVs produce no exhaust.")
child2 = premise("Fossil fuels are the main source of carbon emissions.")
concl = conclusion("Adopting EVs will decrease fossil fuel use.")

addNode(root, child1)
addNode(child1, child2)
addNode(child2, concl)

tree = argumentTree(root)
```

### Manipulate argument nodes

```python
# Add a premise
addNode(root, premise("Countries with high EV adoption show lower emissions growth."))

# Move a subtree
moveSubtree(tree, child1, concl)

# Edit a node's text
editNode(concl, new_text="Governments should invest in EVs.")

# Clone a subtree
clone = cloneSubtree(child1)
addNode(root, clone)

# Prune a node
pruneNode(child1)

# Collapse a subtree
collapseSubtree(child2)
```

### Visualize your argument

```python
from argumentari.visualize import treeToGraph, visualize

graph = treeToGraph(tree.root)
visualize(graph)
```

### Apply argument schemes

```python
from argumentari.schemes import getScheme, argumentScheme

root.setScheme("Argument from Authority", {"Authority": "Dr. Smith", "Statement": "EVs help climate"})
```

### Serialize and deserialize argument trees

```python
from argumentari.io import argumentSerializer

# Serialize to JSON
json_str = argumentSerializer.toJson(tree.root)

# Deserialize from JSON
new_root = argumentSerializer.fromJson(json_str)
```

### Find nodes

```python
matches = findNodes(tree, pattern="EVs")
for node in matches:
    print(node.text)
```

---

## Contact

- GitHub Issues: [Argumentari Issues](https://github.com/literal-gargoyle/argumentari/issues)
- Author: literal-gargoyle

---