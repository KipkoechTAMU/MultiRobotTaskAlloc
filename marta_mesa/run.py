from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from model import ResourceModel, Config
from agent import RobotAgent

# --- Visualization Components ---

# 1. Visualization for the agents and trash
def agent_portrayal(agent):
    if isinstance(agent, RobotAgent):
        # Determine color based on task: 0=Blue, 1=Green, 2=Red, 3=Yellow
        colors = ["#4444FF", "#44FF44", "#FF4444", "#FFFF44"]
        task_color = colors[agent.current_task]
        
        # Portray the robot as a circle with its task color
        return {
            "Shape": "circle",
            "x": agent.pos[0],
            "y": agent.pos[1],
            "r": 0.5,
            "Filled": "true",
            "Color": task_color,
            "Layer": 1
        }
    return {} # No other agent types in this model

# Visualization for the patches (background)
class ResourceVisualization(CanvasGrid):
    def render(self, model):
        # Draw the patches and trash first
        portrayal = super().render(model)
        
        # Define patch areas (similar to the WBT patches)
        patch_coords = [
            (0, 0, 20, 20, "#DDDDFF"), # Patch 0: Light Blue
            (0, 20, 20, 40, "#DDFFDD"), # Patch 1: Light Green
            (20, 0, 40, 20, "#FFDDDD"), # Patch 2: Light Red
            (20, 20, 40, 40, "#FFFFDD")  # Patch 3: Light Yellow
        ]
        
        # Add patches as static background shapes
        for x_min, y_min, x_max, y_max, color in patch_coords:
            portrayal.append({
                "Shape": "rect",
                "x": x_min,
                "y": y_min,
                "w": x_max - x_min,
                "h": y_max - y_min,
                "Color": color,
                "Filled": "true",
                "Layer": 0,
                "text": f"Q: {model.q[patch_coords.index((x_min, y_min, x_max, y_max, color))]:.2f}",
                "text_color": "black"
            })
            
        # Add trash objects
        for trash in model.trash_objects:
            portrayal.append({
                "Shape": "rect",
                "x": trash['x'] - 0.5, # Center the 1x1 box
                "y": trash['y'] - 0.5,
                "w": 1.0,
                "h": 1.0,
                "Color": "#880000", # Dark Red
                "Filled": "true",
                "Layer": 2
            })
            
        return portrayal

# 2. Setup the visualization server
grid_width = 40
grid_height = 40
canvas_element = ResourceVisualization(agent_portrayal, grid_width, grid_height, 500, 500)

# 3. Chart to track resource levels (Q_i)
resource_chart = ChartModule([
    {"Label": "Resource_0", "Color": "#4444FF"},
    {"Label": "Resource_1", "Color": "#44FF44"},
    {"Label": "Resource_2", "Color": "#FF4444"},
    {"Label": "Resource_3", "Color": "#FFFF44"},
], scope="global")


# 4. Function to collect data for the chart
def get_resource_data(model):
    data = {}
    for i in range(Config.NUM_TASKS):
        data[f"Resource_{i}"] = model.q[i]
    return data

# Chart to track population distribution (X_i)
population_chart = ChartModule([
    {"Label": "Pop_0", "Color": "#4444FF"},
    {"Label": "Pop_1", "Color": "#44FF44"},
    {"Label": "Pop_2", "Color": "#FF4444"},
    {"Label": "Pop_3", "Color": "#FFFF44"},
], scope="global")

def get_population_data(model):
    data = {}
    for i in range(Config.NUM_TASKS):
        data[f"Pop_{i}"] = model.x[i]
    return data


# 5. Define the server
server = ModularServer(
    ResourceModel, 
    [canvas_element, resource_chart, population_chart], 
    "Multi-Robot Task Allocation", 
    {"num_robots": 4, "width": grid_width, "height": grid_height, "alpha": 0.2}
)

# 6. Run the server
if __name__ == '__main__':
    server.port = 8521 # Default Mesa port
    print("\nStarting Mesa server on http://127.0.0.1:8521/")
    server.launch()