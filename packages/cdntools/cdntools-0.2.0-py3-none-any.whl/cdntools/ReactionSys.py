import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LogNorm
from matplotlib import patches

# colormap for degradation rates
deg_norm = LogNorm(vmin=1e-4, vmax=1e-3)
deg_cmap = plt.cm.viridis
# edge linewidth
min_interaction_strength = 1e-5
edge_lw_scale = 2
node_s = 500    # scatter size for nodes
halo_scale = 1.2 # >1 means halo ring larger than node

def DefaultRandomProduction():
    return float(np.random.uniform(1e-5, 1e-3))

def DefaultRandomDegradation():
    return float(np.random.uniform(1e-5, 1e-3))

def DefaultRandomKD():
    return float(np.random.uniform(1e-10, 1e-6))

Default_kon = 1e5  # M^-1 s^-1

class ReactionSys:
    def __init__(self, json_file: str = None):
        if json_file is not None:
            self.JSONinit(json_file)
        else:
            pass
    
    def JSONinit(self, json_file: str):
        with open(json_file, 'r') as f:
            data = json.load(f)
            self.Create(data)

    def Create(self, data: dict):
        self.title = data['Title']
        self.type = data['Type']

        # Parse the data based on the type of simulation configured, Production and Degradation (PnD) is currently the only supported type
        if self.type == 'PnD':
            self.monomers = sorted(data['Production'].keys())
            self.name2index = {name: i for i, name in enumerate(self.monomers)}
            self.production = np.array([data['Production'][name] for name in self.monomers])

            # Degradation rates
            self.mono_degradation = np.array([data['Degradation'][name] for name in self.monomers])
            self.dimer_degradation = np.zeros((len(self.monomers), len(self.monomers)))
            self.dimers = []
            for key, value in data['Degradation'].items():
                if '+' in key:
                    m1, m2 = key.split('+')
                    i, j = self.name2index[m1], self.name2index[m2]
                    self.dimer_degradation[i, j] = value
                    self.dimer_degradation[j, i] = value
                    self.dimers.append((i, j))
            self.dimers = np.array(self.dimers)
            self.species_name = self.monomers + [f"{self.monomers[i]}+{self.monomers[j]}" for i, j in self.dimers]
            self.species_name2index = {name: i for i, name in enumerate(self.species_name)}

            # Reaction constants
            self.k_on = np.zeros((len(self.monomers), len(self.monomers)))
            self.k_off = np.ones((len(self.monomers), len(self.monomers)))
            for key, value in data['Reaction'].items():
                m1, m2 = key.split('+')
                i, j = self.name2index[m1], self.name2index[m2]
                
                if 'k_on' in value.keys():
                    self.k_on[i, j] = value['k_on']
                    self.k_on[j, i] = value['k_on']
                    if 'k_off' in value.keys():
                        self.k_off[i, j] = value['k_off']
                        self.k_off[j, i] = value['k_off']
                    else:
                        raise ValueError(f"k_off not specified for reaction {key}, while k_on is specified.")
                
                # Assume a default k_on if only K_D is provided
                elif 'K_D' in value.keys():
                    self.k_on[i, j] = 1e5  # M^-1 s^-1
                    self.k_on[j, i] = 1e5  # M^-1 s^-1
                    self.k_off[i, j] = value['K_D'] * self.k_on[i, j]
                    self.k_off[j, i] = value['K_D'] * self.k_on[j, i]
                else:
                    raise ValueError(f"Neither k_on nor K_D specified for reaction {key}.")

            # Flattened arrays for ODE solving    
            self.dimer_degradation_flat = np.array([self.dimer_degradation[i, j] for i, j in self.dimers])
            self.dimer2index = { (i, j): idx for idx, (i, j) in enumerate(self.dimers) }
            self.dimer2index.update({ (j, i): idx for idx, (i, j) in enumerate(self.dimers)})
            self.k_on_flat = np.array([self.k_on[i, j] for i, j in self.dimers])
            self.k_off_flat = np.array([self.k_off[i, j] for i, j in self.dimers])

            # check if each dimer has both k_on and k_off defined
            for i, j in self.dimers:
                if self.k_on[i, j] == 0:
                    raise ValueError(f"Reaction constants not fully defined for dimer {self.monomers[i]}+{self.monomers[j]}.")
            # check if each dimer defined by reaction has degradation defined
            for i in range(len(self.monomers)):
                for j in range(i, len(self.monomers)):
                    if self.k_on[i, j] > 0 and (i, j) not in self.dimer2index.keys():
                        raise ValueError(f"Dimer degradation rate not defined for dimer {self.monomers[i]}+{self.monomers[j]}.")
            
            # Initial concentrations for ODE solving
            if 'InitConc' in data.keys():
                self.init_conc = data['InitConc']
        
        else:
            raise ValueError(f"Unsupported reaction type: {self.type}")

    def DumpJSON(self, json_file: str = None):
        data = {
            "Title": self.title,
            "Type": self.type,
            "Production": { self.monomers[i]: float(self.production[i]) for i in range(len(self.monomers)) },
            "Degradation": { self.monomers[i]: float(self.mono_degradation[i]) for i in range(len(self.monomers)) }
        }
        for i, j in self.dimers:
            key = f"{self.monomers[i]}+{self.monomers[j]}"
            data["Degradation"][key] = float(self.dimer_degradation[i, j])
        
        reaction = {}
        for i, j in self.dimers:
            key = f"{self.monomers[i]}+{self.monomers[j]}"
            reaction[key] = {
                "k_on": float(self.k_on[i, j]),
                "k_off": float(self.k_off[i, j])
            }
        data["Reaction"] = reaction

        if json_file != None:
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=4)
        
        return data

    # Randomly re-generate production rates for all monomers
    # rand_P should be a function that returns a random production rate when called
    # Default is to use DefaultRandomProduction function defined above
    def RandomIntegration(self, rand_P = DefaultRandomProduction):
        self.production = np.array([rand_P() for _ in self.monomers])


    def _relax_step(self, pos, edges, k=1, repulsion=0.2, dt=0.1):
        """One step of force-directed relaxation."""
        n = pos.shape[0]
        disp = np.zeros_like(pos)
        # Repulsive forces
        for i in range(n):
            for j in range(i + 1, n):
                delta = pos[i] - pos[j]
                dist = np.linalg.norm(delta) + 1e-6
                force = repulsion / dist**2
                disp[i] += delta / dist * force
                disp[j] -= delta / dist * force
        # Attractive forces (edges)
        for i, j in edges:
            delta = pos[i] - pos[j]
            dist = np.linalg.norm(delta) + 1e-6
            force = k * (dist - 1.0)
            disp[i] -= delta / dist * force
            disp[j] += delta / dist * force
        pos += dt * disp
        return pos

    def _relax_positions(self, positions, edges, iterations=1000):
        """Relax positions for a fixed number of iterations."""
        pos = positions.copy()
        for _ in range(iterations):
            pos = self._relax_step(pos, edges)
        return pos

    def _make_widthbar(self, fig):
        # width bar (left) to show mapping between linewidth and K_D
        ticks = [1e-10, 1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4]
        y_pos = np.linspace(0.1, 0.9, len(ticks))
        widthbar_ax = fig.add_axes([0.1, 0.2, 0.06, 0.6])
        for yy, kd in zip(y_pos, ticks):
            lw = (-(np.log10(kd)) + np.log10(min_interaction_strength)) * edge_lw_scale
            lw = max(lw, 0.5)
            widthbar_ax.plot([0.2, 0.8], [yy, yy], color='k', linewidth=lw, solid_capstyle='round')
        widthbar_ax.set_yticks(y_pos)
        widthbar_ax.set_yticklabels([f"{t:.0e}" for t in ticks])
        widthbar_ax.set_xticks([])
        widthbar_ax.set_xlim(0, 1)
        widthbar_ax.set_ylim(0, 1)
        widthbar_ax.set_title("K_D vs width", fontsize=9, x=0)
        for spine in widthbar_ax.spines.values():
            spine.set_visible(False)

    def _animate_relaxation(self, positions, edges, iterations=1000):
        pos = positions.copy()
        line_widths = [(-(np.log10(self.k_off[a, b] / self.k_on[a, b])) + np.log10(min_interaction_strength)) * edge_lw_scale for (a, b) in edges]
        line_colors = [deg_cmap(deg_norm(self.dimer_degradation[a, b])) for (a, b) in edges]
        # homodimer nodes (self-loops)
        homo_nodes = [a for (a, b) in edges if a == b]
        halo_s = node_s * (halo_scale ** 2)  # scatter size is in pt^2

        fig, ax = plt.subplots()
        scat = ax.scatter(pos[:, 0], pos[:, 1], s=node_s, color='lightblue', zorder=2)
        lines = [ax.plot([], [], color=line_colors[i], zorder=1, linewidth=line_widths[i])[0] for i, _ in enumerate(edges)]
        texts = [ax.text(x, y, str(self.monomers[i]), fontsize=12, ha='center', va='center', zorder=3)
                 for i, (x, y) in enumerate(pos)]
        # draw homodimer halo rings using scatter so size is display-unit based (independent of data limits)
        halo = None
        if len(homo_nodes) > 0:
            halo_colors = [deg_cmap(deg_norm(self.dimer_degradation[i, i])) for i in homo_nodes]
            halo_lws = [(-(np.log10(self.k_off[i, i] / self.k_on[i, i])) + np.log10(min_interaction_strength)) * edge_lw_scale for i in homo_nodes]
            halo = ax.scatter(pos[np.array(homo_nodes), 0], pos[np.array(homo_nodes), 1],
                              s=halo_s, facecolors='none', edgecolors=halo_colors,
                              linewidths=halo_lws, zorder=2)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        # ax.axis('off')

        # plot colorbar for degradation rates
        sm = plt.cm.ScalarMappable(cmap=deg_cmap, norm=deg_norm)
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
        cbar.set_label('Degradation Rate', rotation=270, labelpad=15)

        # width bar (left) to show mapping between linewidth and K_D
        self._make_widthbar(fig)

        def update(frame):
            nonlocal pos
            pos = self._relax_step(pos, edges)
            scat.set_offsets(pos)
            for idx, (a, b) in enumerate(edges):
                lines[idx].set_data([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]])
            for i, txt in enumerate(texts):
                txt.set_position((pos[i][0], pos[i][1]))
            # update homodimer halo positions
            if halo is not None:
                halo.set_offsets(pos[np.array(homo_nodes)])
            ax.set_xlim(np.min(pos[:, 0]) - 1, np.max(pos[:, 0]) + 1)
            ax.set_ylim(np.min(pos[:, 1]) - 1, np.max(pos[:, 1]) + 1)

        ani = animation.FuncAnimation(fig, update, frames=iterations, interval=10, blit=False, repeat=False)
        plt.show()

    def PlotSys(self, type: str = 'Circle'):
        node_num = len(self.monomers)
        angles = np.linspace(0, 2 * np.pi, node_num, endpoint=False)
        positions = np.column_stack((np.cos(angles), np.sin(angles)))

        if type == 'Relaxing':
            self._animate_relaxation(positions, self.dimers)
            return
        elif type == 'Relaxed':
            # Use same parameters as animation for consistency
            positions = self._relax_positions(positions, self.dimers)
        elif type == 'Circle':
            pass
        else:
            raise ValueError(f"Unsupported plot type: {type}")

        fig, ax = plt.subplots()

        # plot colorbar for degradation rates
        sm = plt.cm.ScalarMappable(cmap=deg_cmap, norm=deg_norm)
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
        cbar.set_label('Degradation Rate', rotation=270, labelpad=15)

        # width bar (left) to show mapping between linewidth and K_D
        self._make_widthbar(fig)

        # Draw edges
        for a, b in self.dimers:
            x = [positions[a][0], positions[b][0]]
            y = [positions[a][1], positions[b][1]]
            ax.plot(x, y, color=deg_cmap(deg_norm(self.dimer_degradation[a, b])), zorder=1, linewidth=(-(np.log10(self.k_off[a, b] / self.k_on[a, b])) + np.log10(min_interaction_strength))*edge_lw_scale)
        
        # Draw homodimer halo rings (self-loops) using scatter (size in pt^2, independent of data limits)
        halo_s = node_s * (halo_scale ** 2)
        homo_nodes = [a for (a, b) in self.dimers if a == b]
        if len(homo_nodes) > 0:
            halo_colors = [deg_cmap(deg_norm(self.dimer_degradation[i, i])) for i in homo_nodes]
            halo_lws = [(-(np.log10(self.k_off[i, i] / self.k_on[i, i])) + np.log10(min_interaction_strength)) * edge_lw_scale for i in homo_nodes]
            ax.scatter(positions[np.array(homo_nodes), 0], positions[np.array(homo_nodes), 1],
                       s=halo_s, facecolors='none', edgecolors=halo_colors,
                       linewidths=halo_lws, zorder=2)
        
        # Draw nodes
        ax.scatter(positions[:, 0], positions[:, 1], s=node_s, color='lightblue', zorder=2)
        # Draw labels
        for i, (x, y) in enumerate(positions):
            ax.text(x, y, str(self.monomers[i]), fontsize=12, ha='center', va='center', zorder=3)
        ax.set_aspect('equal')
        ax.set_ylim(np.min(positions[:, 1]) - 1, np.max(positions[:, 1]) + 1)
        ax.set_xlim(np.min(positions[:, 0]) - 1, np.max(positions[:, 0]) + 1)
        ax.set_xticks([])
        ax.set_yticks([])
        # ax.axis('off')
        plt.show()

# Example usage:
if __name__ == "__main__":
    reaction_sys = ReactionSys('ExampleReaction.json')
    print("Monomers:", reaction_sys.monomers)
    print("Production rates:", reaction_sys.production)
    print("Monomer degradation rates:", reaction_sys.mono_degradation)
    print("Dimer degradation rates:\n", reaction_sys.dimer_degradation)
    print("k_on matrix:\n", reaction_sys.k_on)
    print("k_off matrix:\n", reaction_sys.k_off)