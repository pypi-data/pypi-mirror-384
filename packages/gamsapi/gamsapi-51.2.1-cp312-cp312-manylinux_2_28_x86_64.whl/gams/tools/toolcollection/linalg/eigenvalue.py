#
# GAMS - General Algebraic Modeling System Python API
#
# Copyright (c) 2017-2025 GAMS Development Corp. <support@gams.com>
# Copyright (c) 2017-2025 GAMS Software GmbH <support@gams.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from gams.tools.toolcollection.tooltemplate  import ToolTemplate

class Eigenvalue (ToolTemplate):

    def __init__(self, system_directory, tool):
        super().__init__(system_directory, tool)
        self.title = 'eigenvalue: This calculates the Eigenvalues of a symmetric positive definite matrix.'
        self.add_posargdef('i',   'id.in:set:1',  'Name of set used in matrix i(*)')
        self.add_posargdef('A',   'id.in:par:2',  'Name of two-dimensional matrix parameter A(i,i)')
        self.add_posargdef('AVal','id.out:par:1', 'Name of one-dimensional parameter to store the Eigenvalues AVal(i)')
        self.add_namedargdef('gdxIn=fileIn.gdx',  'fnExist',    'Name of GDX file that contains symbols i and A', shell_req=True)
        self.add_namedargdef('gdxOut=fileOut.gdx','fnWriteable','Name of GDX file that contains symbol AVal after execution', shell_req=True)

    def execute(self):
        if self.dohelp():
            return

        import gams.transfer as gt
        import numpy as np

        self.process_args()
        i, A, AVal = self.posargs

        m = gt.Container(system_directory=self._system_directory)
        self.read_id_inputs(m, [i, A])
        m[A].domain = [m[i],m[i]]
        a = m[A].toDense()
        upper = self.is_upper_matrix(a)
        eigval = np.linalg.eigvalsh(a, UPLO="U" if upper else "L")
        m.addParameter(AVal,[m[i]], records=eigval)
        self.write_id_outputs(m, AVal)
