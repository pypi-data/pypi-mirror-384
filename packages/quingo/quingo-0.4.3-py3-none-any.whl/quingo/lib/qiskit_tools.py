"""Visualization functions for quantum circuits.

Note, this module requires qiskit to be installed.
"""

from qiskit import QuantumCircuit
from pathlib import Path
from pyqcisim.qcis_to_openqasm import qcis_file_2_qasm_file


def qcis_2_qiskit_qc(qcis_fn: Path):
    """Convert a QCIS file to a qiskit QuantumCircuit object."""
    qasm_fn = qcis_fn.with_suffix(".qasm")
    qasm_str = qcis_file_2_qasm_file(qcis_fn, qasm_fn)
    return QuantumCircuit.from_qasm_file(str(qasm_fn))


def draw_circ(qcis_fn: Path, output="mpl"):
    """Draw the quantum circuit using qiskit.
    Use the output parameter to choose the drawing format:

        **text**: ASCII art TextDrawing that can be printed in the console.

        **mpl**: images with color rendered purely in Python using matplotlib.

        **latex**: high-quality images compiled via latex.

        **latex_source**: raw uncompiled latex output.
    """
    qasm_fn = qcis_fn.with_suffix(".qasm")
    qasm_str = qcis_file_2_qasm_file(qcis_fn, qasm_fn)
    qc = QuantumCircuit.from_qasm_file(str(qasm_fn))
    return qc.draw(output=output)


def estimate_resource(qcis_fn: Path):
    """估算量子电路的资源使用情况。

    该函数将 QCIS 文件转换为 Qiskit QuantumCircuit 对象，并统计电路的关键资源指标。

    Parameters
    ----------
    qcis_fn : Path
        QCIS 格式的量子电路文件路径。

    Returns
    -------
    tuple
        包含三个元素的元组：

        - depth (int): 电路深度，即并行执行时所需的最少时间步数。
          表示电路中最长的门序列长度。

        - num_qubits (int): 电路中使用的量子比特数量（不包括经典比特）。

        - ops_count (OrderedDict): 有序字典，包含电路中各种门操作的统计数量。
          键为门操作名称（如 'h', 'cx', 'measure'），值为该操作的出现次数。

    Examples
    --------
    >>> from pathlib import Path
    >>> qcis_fn = Path('/path/to/bell.qcis')
    >>> depth, num_qubits, ops = estimate_resource(qcis_fn)
    >>> print(f"电路深度: {depth}, 量子比特数: {num_qubits}")
    电路深度: 3, 量子比特数: 2
    >>> print(f"门操作统计: {dict(ops)}")
    门操作统计: {'measure': 2, 'h': 1, 'cx': 1}

    Notes
    -----
    - 该函数会在 QCIS 文件的同目录下生成一个同名的 .qasm 文件作为中间转换结果。
    - 电路深度是评估量子算法运行时间的重要指标，深度越小通常意味着算法越快。
    - 量子比特数表示电路所需的量子资源数量，不包括用于测量结果存储的经典比特。
    """
    qc = qcis_2_qiskit_qc(qcis_fn)
    return qc.depth(), qc.num_qubits, qc.count_ops()
