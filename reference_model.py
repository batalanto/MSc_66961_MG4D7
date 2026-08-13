"""
Reference Petri nets (article 9 & 12) used during conformance checking.
"""

from pm4py.objects.process_tree.obj import ProcessTree, Operator
from pm4py.objects.conversion.process_tree import converter as pt_converter


def _leaf(label, parent):
    """Creates a leaf node."""
    return ProcessTree(label=label, parent=parent)


def _seq(labels_or_nodes):
    """Creates a sequence node."""
    node = ProcessTree(operator=Operator.SEQUENCE)
    for x in labels_or_nodes:
        child = x if isinstance(x, ProcessTree) else ProcessTree(label=x)
        child.parent = node
        node.children.append(child)
    return node


def _par(labels):
    """Creates a parallel node."""
    node = ProcessTree(operator=Operator.PARALLEL)
    for a in labels:
        node.children.append(_leaf(a, node))
    return node


ART_12_ACTIVITIES = [
    "enable logging", "record risk-relevant events", "record post-market events",
    "record operational events", "record use period", "record reference DB",
    "record matching input", "record verifier identity",
]

# grouped by article 9 section
ART_9_SETUP = ["Establish RMS", "Implement RMS"]
ART_9_CORE = [
    "Identify risks", "Analyse risks", "Estimate risks", "Evaluate risks",
    "Adopt measures", "Reduce via design", "Implement mitigation", "Judge residual risk",
]
ART_9_TESTING = ["Define metrics", "Test AI system"]
ART_9_PARALLEL = [
    "Evaluate post-market data", "Provide info", "Provide training",
    "Document RMS", "Maintain RMS",
]


def build_art12_net():
    """Builds the article 12 reference net"""
    root = ProcessTree(operator=Operator.PARALLEL)
    for a in ART_12_ACTIVITIES:
        root.children.append(_leaf(a, root))
    return pt_converter.apply(root)


def build_art9_net():
    # iterative risk management loop
    core_seq = _seq(ART_9_CORE)
    loop = ProcessTree(operator=Operator.LOOP)
    core_seq.parent = loop
    loop.children = [core_seq, ProcessTree(label=None, parent=loop)]
    # combine all sections
    root = _seq([_seq(ART_9_SETUP), loop, _seq(ART_9_TESTING), _par(ART_9_PARALLEL)])
    return pt_converter.apply(root)


def save_net_image(net, im, fm, path):
    """Saves a Petri-net as an image"""
    try:
        import pm4py
        pm4py.save_vis_petri_net(net, im, fm, path)
        return True
    except Exception as e:
        print(f"  could not draw {path}, Graphviz may be missing. {e}")
        return False


if __name__ == "__main__":
    save_net_image(*build_art12_net(), "art_12_net.png")
    save_net_image(*build_art9_net(), "art_9_net.png")
    print("built both nets and saved the images")
