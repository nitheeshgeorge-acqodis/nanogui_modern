# OpenGL/Metal rendering test: render a spinning cube with MSAA

import sys
sys.path.append('python')
import nanogui
import nanogui as ng
from nanogui import glfw
import numpy as np


class MyScreen(ng.Screen):
    def __init__(self):
        ng.Screen.__init__(self,
            size=[512, 512],
            caption="Unnamed"
        )

        if ng.api == 'opengl':
            vertex_program = '''
                #version 330
                in vec3 position;
                in vec4 color;
                out vec4 color_frag;
                uniform mat4 mvp;

                void main() {
                    gl_Position = mvp * vec4(position, 1.0);
                    color_frag = color;
                }
            '''

            fragment_program = '''
                #version 330
                in vec4 color_frag;
                out vec4 fragColor;

                void main() {
                    fragColor = color_frag;
                }
            '''
        elif ng.api == 'metal':
            vertex_program = '''
                using namespace metal;

                struct VertexOut {
                    float4 position [[position]];
                    float4 color;
                };

                vertex VertexOut vertex_main(const device packed_float3 *position,
                                             const device float4 *color,
                                             constant float4x4 &mvp,
                                             uint id [[vertex_id]]) {
                    VertexOut vert;
                    vert.position = mvp * float4(position[id], 1.f);
                    vert.color = color[id];
                    return vert;
                }
            '''

            fragment_program = '''
                using namespace metal;

                struct VertexOut {
                    float4 position [[position]];
                    float4 color;
                };

                fragment float4 fragment_main(VertexOut vert [[stage_in]]) {
                    return vert.color;
                }
            '''

        self.color_target = ng.Texture(
            pixel_format=self.pixel_format(),
            component_format=self.component_format(),
            size=self.framebuffer_size(),
            flags=ng.Texture.TextureFlags.RenderTarget,
            samples=4
        )

        self.depth_target = ng.Texture(
            pixel_format=ng.Texture.PixelFormat.Depth,
            component_format=ng.Texture.ComponentFormat.Float32,
            size=self.framebuffer_size(),
            flags=ng.Texture.TextureFlags.RenderTarget,
            samples=4
        )

        self.render_pass = ng.RenderPass(
            color_targets=[self.color_target],
            depth_target=self.depth_target,
            blit_target=self
        )

        self.shader = ng.Shader(
            self.render_pass,
            "test_shader",
            vertex_program,
            fragment_program
        )

        p = np.array([
            [-1, 1, 1], [-1, -1, 1],
            [1, -1, 1], [1, 1, 1],
            [-1, 1, -1], [-1, -1, -1],
            [1, -1, -1], [1, 1, -1]],
            dtype=np.float32
        )

        color = np.array([
            [0, 1, 1, 1], [0, 0, 1, 1],
            [1, 0, 1, 1], [1, 1, 1, 1],
            [0, 1, 0, 1], [0, 0, 0, 1],
            [1, 0, 0, 1], [1, 1, 0, 1]],
            dtype=np.float32
        )

        indices = np.array([
            3, 2, 6, 6, 7, 3,
            4, 5, 1, 1, 0, 4,
            4, 0, 3, 3, 7, 4,
            1, 5, 6, 6, 2, 1,
            0, 1, 2, 2, 3, 0,
            7, 6, 5, 5, 4, 7],
            dtype=np.uint32
        )

        self.shader.set_buffer("position", p)
        self.shader.set_buffer("color", color)
        self.shader.set_buffer("indices", indices)

    def draw_contents(self):
        with self.render_pass:
            view = ng.Matrix4f.look_at(
                origin=[0, -2, -10],
                target=[0, 0, 0],
                up=[0, 1, 0]
            )

            model = ng.Matrix4f.rotate(
                [0, 1, 0],
                glfw.getTime()
            )

            fbsize = self.framebuffer_size()
            proj = ng.Matrix4f.perspective(
                fov=25 * np.pi / 180,
                near=0.1,
                far=20,
                aspect=fbsize[0] / float(fbsize[1])
            )

            mvp = proj @ view @ model
            self.shader.set_buffer("mvp", mvp.T) # -> col-major
            with self.shader:
                self.shader.draw_array(ng.Shader.PrimitiveType.Triangle,
                                       0, 36, indexed=True)

    def keyboard_event(self, key, scancode, action, modifiers):
        if super(MyScreen, self).keyboard_event(key, scancode,
                                              action, modifiers):
            return True
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            self.set_visible(False)
            return True
        return False

    def resize_event(self, size):
        self.render_pass.resize(self.framebuffer_size())
        super(MyScreen, self).resize_event(size)
        return True

def run():
    ng.init()
    s = MyScreen()
    s.set_visible(True)
    ng.mainloop(1 / 60.0 * 1000)
    ng.shutdown()

if __name__ == '__main__':
    run()
