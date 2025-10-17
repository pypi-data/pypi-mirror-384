import numpy as np
import time
import matplotlib.pyplot as plt
from .ReactionSys import ReactionSys
from .ReactionSys import DefaultRandomKD, DefaultRandomProduction, DefaultRandomDegradation, Default_kon

# generate a random connected undirected graph with given number of nodes and edges
def RandomNet (node_num: int, edge_num: int, seed = time.time(), homodimer_num = 0):
    if edge_num < node_num - 1:
        raise ValueError("Number of edges must be at least n-1 to ensure connectivity.")
    if edge_num > node_num * (node_num - 1) // 2:
        print ("Warning: Too many edges requested, reducing to maximum possible for simple graph.")
        edge_num = node_num * (node_num - 1) // 2

    np.random.seed(int(seed) % (2**32 - 1))
    
    edges = []
    # generate a random spanning tree
    for tree_size in range(1, node_num):
        parent = np.random.randint(0, tree_size)
        edges.append((parent, tree_size))

    # add random edges until reaching the desired edge count
    existing = set(edges)
    possible = {(i, j) for i in range(node_num) for j in range(i+1, node_num)}
    possible -= set((min(a, b), max(a, b)) for a, b in existing)
    needed = edge_num - len(edges)
    new_edges = np.random.choice(len(possible), needed, replace=False)
    possible = list(possible)
    for idx in new_edges:
        edges.append(possible[idx])

    # add homodimers if needed
    if homodimer_num > 0:
        homodimer_candidates = list(range(node_num))
        np.random.shuffle(homodimer_candidates)
        for i in range(min(homodimer_num, node_num)):
            edges.append((homodimer_candidates[i], homodimer_candidates[i]))

    return np.array(edges)

# plot given graph
def GraphCircularPlot (edges: np.ndarray, node_name:np.ndarray):
    node_num = len(node_name)

    # Calculate node positions in a circle
    angles = np.linspace(0, 2 * np.pi, node_num, endpoint=False)
    positions = np.column_stack((np.cos(angles), np.sin(angles)))

    fig, ax = plt.subplots()
    # Draw edges
    for a, b in edges:
        x = [positions[a][0], positions[b][0]]
        y = [positions[a][1], positions[b][1]]
        ax.plot(x, y, color='gray', zorder=1)
    # Draw nodes
    ax.scatter(positions[:, 0], positions[:, 1], s=500, color='lightblue', zorder=2)
    # Draw labels
    for i, (x, y) in enumerate(positions):
        ax.text(x, y, str(node_name[i]), fontsize=12, ha='center', va='center', zorder=3)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.show()

# generate reaction terms
def RandomReactionSys (mono_num: int, binding_num: int, seed = time.time(), homodimer_num = 0) -> ReactionSys:
    data = {
        "Title": f"RandomReactionSystem_{mono_num}Monomers_{binding_num}Bindings_{seed}Seed_{homodimer_num}Homodimers",
        "Type": "PnD"
    }
    np.random.seed(int(seed) % (2**32 - 1))
    edges = RandomNet(mono_num, binding_num, np.random.randint(0, 2**32 - 1), homodimer_num=homodimer_num)
    monomers = [chr(65 + i) for i in range(mono_num)]

    production = { mono: DefaultRandomProduction() for mono in monomers }
    data["Production"] = production

    mono_degradation = { mono: DefaultRandomDegradation() for mono in monomers }
    dimer_degradation = {}
    for a, b in edges:
        dimer_degradation[f"{monomers[a]}+{monomers[b]}"] = DefaultRandomDegradation()
    data["Degradation"] = { **mono_degradation, **dimer_degradation }

    reaction = {}
    for a, b in edges:
        k_on = Default_kon
        K_D = DefaultRandomKD()
        k_off = k_on * K_D
        reaction[f"{monomers[a]}+{monomers[b]}"] = { "k_on": k_on, "k_off": k_off }
    data["Reaction"] = reaction

    system = ReactionSys()
    system.Create(data)
    return system

# example usage
if __name__ == "__main__":
    num_nodes = 15
    num_edges = 21
    '''edges = RandomNet(num_nodes, num_edges)
    node_names = np.array([chr(65 + i) for i in range(num_nodes)])  # A, B, C, ...
    GraphCircularPlot(edges, node_names)'''
    reaction_sys = RandomReactionSys(num_nodes, num_edges, seed=42)
    reaction_sys.DumpJSON("RandomReactionSystem.json")
    ani = reaction_sys.PlotSys(type='Relaxing')
    plt.show()
