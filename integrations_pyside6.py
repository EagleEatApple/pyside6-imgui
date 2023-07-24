#!/usr/bin/env python
# -*- coding: utf-8 -*-

# refert to https://github.com/henkeldi/opengl_cheatsheet/blob/master/test/test_opengl.py
import sys

import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QTimerEvent
from PySide6.QtGui import QCloseEvent, QSurfaceFormat
from OpenGL.GL import *
import imgui

from pyside6 import PySide6Renderer
from testwindow import show_test_window


class ImGuiWidget(QOpenGLWidget):
    def __init__(self) -> None:
        super().__init__()
        self.startTimer(20)
        # initialize OpenGL profile
        _format = QSurfaceFormat()
        _format.setDepthBufferSize(24)
        _format.setSamples(4)
        _format.setVersion(4, 6)
        _format.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(_format)

    def timerEvent(self, event: QTimerEvent) -> None:
        self.update()

    def initializeGL(self) -> None:
        self.psize = 30.0

        # initialize shaders
        self.program = glCreateProgram()
        self.addShader('shader.vs', GL_VERTEX_SHADER)
        self.addShader('shader.frag', GL_FRAGMENT_SHADER)
        glLinkProgram(self.program)
        glUseProgram(self.program)

        # initialize vertex attributes
        vertices = np.array([-0.5, -0.5, 0.5, -0.5, -0.5,
                            0.5, 0.5, 0.5], dtype=np.float32)
        colors = np.array([255, 0, 0, 0, 255, 0, 0, 0, 255,
                          0, 255, 255, 255, 255, 0], dtype=np.uint8)
        indices = np.array([0, 1, 2, 2, 1, 3], dtype=np.uint8)
        ibo_data = np.array([6, 1, 0, 0, 0], dtype=np.uint32)

        self.buf = np.empty(4, dtype=np.uint32)
        glCreateBuffers(len(self.buf), self.buf)
        glNamedBufferStorage(self.buf[0], vertices.nbytes, vertices, 0)
        glNamedBufferStorage(self.buf[1], colors.nbytes, colors, 0)
        glNamedBufferStorage(self.buf[2], indices.nbytes, indices, 0)
        glNamedBufferStorage(self.buf[3], ibo_data.nbytes, ibo_data, 0)

        self.vao = GLuint()
        glCreateVertexArrays(1, self.vao)

        glVertexArrayAttribFormat(self.vao, 0, 2, GL_FLOAT, GL_FALSE, 0)
        glVertexArrayVertexBuffer(self.vao, 0, self.buf[0], 0, 2*4)
        glEnableVertexArrayAttrib(self.vao, 0)
        glVertexArrayAttribBinding(self.vao, 0, 0)

        glVertexArrayAttribFormat(self.vao, 1, 3, GL_UNSIGNED_BYTE, GL_TRUE, 0)
        glVertexArrayVertexBuffer(self.vao, 1, self.buf[1], 0, 3)
        glEnableVertexArrayAttrib(self.vao, 1)
        glVertexArrayAttribBinding(self.vao, 1, 1)

        glVertexArrayElementBuffer(self.vao, self.buf[2])

        glBindVertexArray(self.vao)
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, self.buf[3])

        # initialize imgui
        imgui.create_context()
        self.impl = PySide6Renderer(self)

    def paintGL(self) -> None:
        glClear(GL_COLOR_BUFFER_BIT)
        glClearColor(0.0, 0.0, 0.0, 0.0)

        glPointSize(self.psize)
        glDrawArrays(GL_POINTS, 0, 6)
        glDrawElementsIndirect(
            GL_TRIANGLES, GL_UNSIGNED_BYTE, ctypes.c_void_p(0*20))

        # define imgui elements
        self.impl.process_inputs()
        imgui.new_frame()

        show_test_window()

        imgui.begin("Controls")
        point_size = int(self.psize)
        changed, point_size = imgui.slider_int(
            "Point size", point_size, 1, 100)
        self.psize = float(point_size)
        imgui.end()

        # render imgui
        imgui.render()
        self.impl.render(imgui.get_draw_data())

    def addShader(self, file_name: str, type: GLenum) -> None:
        shader = glCreateShader(type)
        with open(file_name, 'r') as file:
            glShaderSource(shader, file.read())
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            print(glGetShaderInfoLog(shader))
            raise RuntimeError("glCompileShader failed to compile: %s", error)
        glAttachShader(self.program, shader)

    def closeEvent(self, event: QCloseEvent) -> None:
        # clean up GPU resources
        self.makeCurrent()
        glDeleteVertexArrays(1, self.vao)
        glDeleteBuffers(4, self.buf)
        self.impl.shutdown()
        return super().closeEvent(event)


def Run() -> None:
    app = QApplication(sys.argv)
    widget = ImGuiWidget()
    widget.setWindowTitle("ImGui/PySide6 QOpenGLWidget example")
    widget.resize(1280, 800)
    widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    Run()
