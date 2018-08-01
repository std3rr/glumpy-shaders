import numpy as np

from glumpy import app  # application context, windows, input, events
from glumpy import gloo # buffers and bridge to the GPU
from glumpy import glm  # helpers for matrix operations
from glumpy import gl   # basic gl primitives and functions

# import os
## My Intel graphics chip is psycho with sharing contexts, so ...
# os.environ["PYGLET_SHADOW_WINDOW"] = "0"
## Had some problem getting glfw backend to work, forced pyglet fallback
# app.use("pyglet")

#----------------------------------------------------------------------
# Define our shader programs.
# First the vertex source program ...
vertex = """
    uniform mat4   model;         // Model matrix
    uniform mat4   view;          // View matrix
    uniform mat4   projection;    // Projection matrix
    attribute vec4 color;         // Vertex color
    attribute vec3 position;      // Vertex position
    varying vec3   v_position;    // Interpolated vertex position (out)
    varying vec4   v_color;       // Interpolated fragment color (out)
    varying vec4   v_trans;       // model transformed (out)

    void main()
    {
        v_color = color;
        v_position = position;
        v_trans = model * vec4(position,1.0);

        // As matrix multiplication is not commutative
        // and we now control this our self, the order is important.
        gl_Position = projection * view * model * vec4(position,1.0);
    }
"""
# ... then the fragment source program, getting sort of input from above
fragment = """
    varying vec4 v_color;     // Interpolated fragment color (in)
    varying vec3 v_position;  // Interpolated vertex position (in)
    varying vec4 v_trans;     // model transformed (in)

    void main()
    {
        float xy = min( abs(v_position.x), abs(v_position.y));
        float xz = min( abs(v_position.x), abs(v_position.z));
        float yz = min( abs(v_position.y), abs(v_position.z));
        float b = 0.85;
        float c = 0.70;
        float a = 0.98;

        if ((xy > a) || (xz > a) || (yz > a))
            gl_FragColor = vec4(0,0,0,v_trans.z+1.0);
        else if ((xy > b) || (xz > b) || (yz > b))
            gl_FragColor = vec4( v_trans.z,
                                 v_trans.z,
                                 v_trans.z,
                                 v_trans.z+1.0);
        else if((xy < c) && (xz < c) && (yz < c))
            discard;
        else
            gl_FragColor = v_color*0.85;
    }
"""
#
#-----------------------------------------------------------------------

# Create a window with white background
window = app.Window(width=512, height=512, color=(1, 1, 1, 1))

#-----------------------------------------------------------------
# Register some event listeners
#
# on_resize on my windows machine is bugged through pyglet backend
@window.event
def on_resize(width, height):
   ratio = float( width / height )
    # update the projection matrix
   cube['projection'] = glm.perspective(45.0, ratio, 2.0, 100.0)

@window.event
def on_draw(dt):
    global phi, theta
    window.clear()
    # draw the cube using GL_TRIANGLES primitives
    cube.draw(gl.GL_TRIANGLES, I)

    # Make cube rotate
    theta += 1.0 # degrees
    phi += 1.0 # degrees
    # create an identity matrix and rotate
    model = np.eye(4, dtype=np.float32)
    glm.rotate(model, theta, 0, 0, 1)
    glm.rotate(model, phi, 0, 1, 0)
    # send to gpu through our binded structure
    cube['model'] = model

@window.event
def on_init():
    # When dealing with 3d rotation we really want depth testing
    gl.glEnable(gl.GL_DEPTH_TEST)
#
#---------------------------------------------------------------

# Create structures and lists of virtices
V = np.zeros(8, [("position", np.float32, 3),
                 ("color", np.float32, 4)])
# X, Y, Z
V["position"] = [[ 1, 1, 1], [-1, 1, 1], [-1,-1, 1], [ 1,-1, 1],
                 [ 1,-1,-1], [ 1, 1,-1], [-1, 1,-1], [-1,-1,-1]]
# RGBA
V["color"]    = [[0, 1, 1, 1], [0, 0, 1, 1], [0, 0, 0, 1], [0, 1, 0, 1],
                 [1, 1, 0, 1], [1, 1, 1, 1], [1, 0, 1, 1], [1, 0, 0, 1]]

# polygon face indices
I = np.array([0,1,2, 0,2,3,  0,3,4, 0,4,5,  0,5,6, 0,6,1,
              1,6,7, 1,7,2,  7,4,3, 7,3,2,  4,7,6, 4,6,5], dtype=np.uint32)

# Buffers for vertex attribute and index data to be transfered to GPU
V = V.view(gloo.VertexBuffer)
I = I.view(gloo.IndexBuffer)

# Link and compile shaders into a program
cube = gloo.Program(vertex, fragment)
# Bind a vertex buffer to the program,
# matching buffer record names with program attributes.
cube.bind(V)

# Move the camera back a bit
cube['view'] = glm.translation(0, 0, -5)

# global degree init for y and z
phi, theta = 40, 30

# Run the mainloop with a 60fps cap
app.run(framerate=60)
