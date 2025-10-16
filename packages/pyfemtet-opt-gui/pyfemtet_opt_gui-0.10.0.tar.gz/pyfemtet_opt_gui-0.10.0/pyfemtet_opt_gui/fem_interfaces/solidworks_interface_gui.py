import os
import re
from time import sleep, time

# noinspection PyUnresolvedReferences
from pythoncom import com_error
from win32com.client import Dispatch, CDispatch
# noinspection PyUnresolvedReferences
from pythoncom import CoInitialize, CoUninitialize

# noinspection PyUnresolvedReferences
from PySide6.QtWidgets import *

from pyfemtet._util.solidworks_variable import SolidworksVariableManager

import pyfemtet_opt_gui
from pyfemtet_opt_gui.common.expression_processor import Expression
from pyfemtet_opt_gui.common.symbol_support import convert, revert
from pyfemtet_opt_gui.common.return_msg import *
from pyfemtet_opt_gui.fem_interfaces.femtet_interface_gui import (
    _search_process,
    FemtetInterfaceGUI,
    logger
)

_sw: CDispatch | None = None


def launch_solidworks() -> bool:
    global _sw

    CoInitialize()

    try:
        _sw = Dispatch('Sldworks.application')
    except com_error:
        return False

    try:
        _sw.Visible = True
    except com_error:
        return False

    return True


def get_name_from_equation(equation: str):
    pattern = r'^\s*"(.+?)"\s*$'  # " で囲まれた中身
    matched = re.match(pattern, equation.split('=')[0])
    if matched:
        return convert(matched.group(1))
    else:
        return None


def get_expression_from_equation(equation: str):
    assert '=' in equation
    expression: str = equation.removeprefix(equation.split('=')[0] + '=')  # 最初の = 以降を取得

    # # 1) 式全体が "..." だけの場合
    # whole_match = re.match(r'^\s*"(.+?)"\s*$', expression)  # " で囲まれた中身
    # if whole_match:
    #     inner = whole_match.group(1)
    #     converted_expression = f'"{convert(inner)}"'

    # 2) 部分的に "..." が含まれる場合：すべての "..." を convert して置換
    def repl(m: re.Match) -> str:
        inner = m.group(1)
        return f'"{convert(inner)}"'

    # 非貪欲で " 内だけを拾う
    converted_expression = re.sub(r'"(.+?)"', repl, expression)

    # " を消す
    converted_expression = converted_expression.replace('"', '')
    expr: Expression = Expression(converted_expression)
    return expr


class SolidWorksInterfaceGUI(FemtetInterfaceGUI):

    # ===== process & object handling =====
    @classmethod
    def get_femtet(cls, progress: QProgressDialog = None) -> tuple[CDispatch | None, ReturnType]:
        cls.get_sw(progress)
        return FemtetInterfaceGUI.get_femtet(progress)

    @classmethod
    def get_sw(cls, progress: QProgressDialog = None) -> tuple[CDispatch | None, ReturnType]:

        global _sw

        if progress is not None:
            progress.setLabelText('Solidworks を起動しています...')

        should_restart = False

        # 一度も Dispatch されていない場合
        if _sw is None:
            should_restart = True

        # Dispatch されたが現在 alive ではない場合
        elif SolidWorksInterfaceGUI.get_sw_connection_state() != ReturnMsg.no_message:
            should_restart = True

        # 再起動する
        if should_restart:
            logger.info('Solidworks を起動しています。')
            succeeded = launch_solidworks()

        else:
            succeeded = True

        if succeeded:
            return _sw, ReturnMsg.no_message

        else:
            return None, ReturnMsg.Error.femtet_connection_failed

    @classmethod
    def get_connection_state(cls) -> ReturnType:

        ret_msg = cls.get_sw_connection_state()
        if ret_msg != ReturnMsg.no_message:
            return ret_msg
        return FemtetInterfaceGUI.get_connection_state()

    @classmethod
    def get_sw_connection_state(cls) -> ReturnType:

        # プロセスが存在しない場合
        if not _search_process('SLDWORKS.exe'):
            return ReturnMsg.Error.sw_process_not_found

        # 1 度も Dispatch されていない場合
        if _sw is None:
            return ReturnMsg.Error.sw_connection_not_yet

        # メソッドへのアクセスを試みる
        try:
            # noinspection PyUnusedLocal
            visible = _sw.Visible

        # Dispatch オブジェクトは存在するが
        # メソッドにアクセスできない場合
        except com_error:
            return ReturnMsg.Error.sw_connection_error

        return ReturnMsg.no_message

    # ===== Parameter =====
    @classmethod
    def get_variables(cls) -> tuple[dict[str, Expression], ReturnType]:

        # check Connection
        ret = SolidWorksInterfaceGUI.get_sw_connection_state()
        if ret != ReturnMsg.no_message:
            return {}, ret

        # get solidworks
        swModel = _sw.ActiveDoc
        if swModel is None:
            return {}, ReturnMsg.no_message

        # Get equations
        mgr = SolidworksVariableManager()
        equations: set[str] = mgr.get_equations_recourse(
            swModel=swModel,
            global_variables_only=False,
        )

        # Parse equations
        out = dict()
        for eq in equations:
            logger.debug(f'===== {eq} =====')
            name = get_name_from_equation(eq)
            expr: Expression = get_expression_from_equation(eq)

            if expr.is_number():
                out.update({name: expr})
            # out.update({name: expr})

        return out, ReturnMsg.no_message

    @classmethod
    def apply_variables(cls, variables: dict[str, float | str]) -> tuple[ReturnType, str | None]:

        # check Connection
        ret = SolidWorksInterfaceGUI.get_sw_connection_state()
        if ret != ReturnMsg.no_message:
            return ret, ''

        # get solidworks
        swModel = _sw.ActiveDoc
        if swModel is None:
            ret_msg = ReturnMsg.Error.sw_no_active_doc
            return ret_msg, ''

        # Construct SWVariables:
        x = {revert(name): revert(str(expression)) for name, expression in variables.items()}

        # Update variables
        mgr = SolidworksVariableManager(logger)
        mgr.update_global_variables_recourse(swModel=swModel, x=x)

        # Check the variables updated
        remaining_variables = (set(x.keys()) - mgr.updated_objects)
        if len(remaining_variables) > 0:
            return ReturnMsg.Error.sw_remaining_variable, ','.join(remaining_variables)

        # sw モデルを更新する
        result = swModel.EditRebuild3
        if not result:
            return ReturnMsg.Error.sw_model_error, ''

        # 出力すべき x_t パスがあるかチェック
        ret, x_t_path = cls._get_last_x_t_path()
        if ret != ReturnMsg.no_message:
            return ret, ''

        # 存在するファイルならば上書きするために削除
        if os.path.isfile(x_t_path):
            os.remove(x_t_path)

        # 存在しないファイルならばファイルパスを新たに作成
        else:

            # プロジェクトファイル名を取得
            (file_paths, model_name), ret_msg = cls.get_name()
            if ret_msg != ReturnMsg.no_message:
                return ret_msg, ''

            # プロジェクトファイルと同名の x_t
            femprj_path: str = file_paths[0]
            x_t_path = femprj_path.lower().removesuffix('.femprj') + '.x_t'

            # Femtet の LastXTPath を更新
            cls._set_last_x_t_path(x_t_path)

        # x_t を出力
        if os.path.exists(x_t_path):
            os.remove(x_t_path)
        swModel.SaveAs(x_t_path)

        # 30 秒待っても x_t ができてなければエラー(COM なのでありうる)
        timeout = 30
        start = time()
        while True:
            if os.path.isfile(x_t_path):
                break
            if time() - start > timeout:
                return ReturnMsg.Error.sw_cannot_export_model, ''
            sleep(1)

        # Femtet モデルを更新する
        return cls._rebuild_model()

    # ===== project handling =====
    @classmethod
    def get_name(cls) -> tuple[tuple[list[str], str] | None, ReturnType]:
        names, ret_msg = FemtetInterfaceGUI.get_name()
        if ret_msg != ReturnMsg.no_message:
            return None, ret_msg
        (paths, model_name) = names

        sldprt_path, ret_msg = cls.get_sw_name()
        if ret_msg != ReturnMsg.no_message:
            return None, ret_msg

        paths.append(sldprt_path)
        return (paths, model_name), ret_msg

    @classmethod
    def get_sw_name(cls) -> tuple[str | None, ReturnType]:

        # check Connection
        ret = SolidWorksInterfaceGUI.get_sw_connection_state()
        if ret != ReturnMsg.no_message:
            return None, ret

        swDoc = _sw.ActiveDoc
        if swDoc is None:
            return '.sldprt ファイルが開かれていません', ReturnMsg.no_message

        path = swDoc.GetPathName
        if path is None or not os.path.isfile(path):
            return None, ReturnMsg.Error.sw_sldprt_not_found

        return path, ReturnMsg.no_message

    @classmethod
    def save_femprj(cls) -> tuple[bool, tuple[ReturnType, str]]:
        succeeded, (r, a) = FemtetInterfaceGUI.save_femprj()
        if r != ReturnMsg.no_message:
            return False, (r, a)

        succeeded, (r, a) = cls.save_sldprt()
        if r != ReturnMsg.no_message:
            return False, (r, a)

        return True, (ReturnMsg.no_message, '')

    @classmethod
    def save_sldprt(cls) -> tuple[bool, tuple[ReturnType, str]]:

        # check Connection
        ret = SolidWorksInterfaceGUI.get_sw_connection_state()
        if ret != ReturnMsg.no_message:
            return False, (ret, '')

        # 上書き保存
        _sw.ActiveDoc.Save2(True)  # silent, always returns True

        return True, (ReturnMsg.no_message, '')

    @classmethod
    def open_sample(cls, progress: QProgressDialog = None) -> tuple[ReturnType, str]:

        if progress is not None:
            progress.setLabelText('Femtet のサンプルファイルを開いています...')

        # get path
        # noinspection PyTypeChecker
        path = os.path.abspath(
            os.path.join(
                os.path.dirname(pyfemtet_opt_gui.__file__),
                'assets', 'samples', 'cad_ex01_SW.femprj'
            )
        ).replace(os.path.altsep, os.path.sep)

        # check Femtet Connection
        ret = SolidWorksInterfaceGUI.get_sw_connection_state()
        if ret != ReturnMsg.no_message:
            return ret, path

        succeeded = cls._load_femprj(path)
        if not succeeded:
            return ReturnMsg.Error.cannot_open_sample_femprj, path

        if progress is not None:
            progress.setLabelText('Solidworks のサンプルファイルを開いています...')

        # get path
        # noinspection PyTypeChecker
        path2 = os.path.abspath(
            os.path.join(
                os.path.dirname(pyfemtet_opt_gui.__file__),
                'assets', 'samples', 'cad_ex01_SW.sldprt'
            )
        ).replace(os.path.altsep, os.path.sep)

        # check Femtet Connection
        ret = SolidWorksInterfaceGUI.get_sw_connection_state()
        if ret != ReturnMsg.no_message:
            return ret, ', '.join([path, path2])

        swDocPART = 1  # https://help.solidworks.com/2023/english/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swDocumentTypes_e.html
        _sw.OpenDoc(path2, swDocPART)
        if not succeeded:
            return ReturnMsg.Error.cannot_open_sample_femprj, ', '.join([path, path2])

        return ReturnMsg.no_message, ', '.join([path, path2])


if __name__ == '__main__':
    __Femtet, __ret_msg = SolidWorksInterfaceGUI.get_femtet()
    print(__ret_msg)
    print(__Femtet)

    __ret_msg, __a_msg = SolidWorksInterfaceGUI.open_sample()
    print(__ret_msg)
    print(__a_msg)

    __variables, __ret_msg = SolidWorksInterfaceGUI.get_variables()
    print(__ret_msg)
    print(__variables)

    __ret_msg, __a_msg = SolidWorksInterfaceGUI.apply_variables(
        dict(A=10, B=10)
    )
    print(__ret_msg)
    print(__a_msg)
