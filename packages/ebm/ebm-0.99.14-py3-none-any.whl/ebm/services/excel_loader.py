import logging

import win32com.client
from loguru import logger
from win32com.universal import com_error


def access_excel_sheet(workbook_name: str, sheet_name: str) -> win32com.client.CDispatch:
    """
   Opens the specified sheet in the specified workbook using COM.

   Parameters
   ----------
   workbook_name : str
       The name of the workbook.
   sheet_name : str
       The name of the sheet.

   Returns
   -------
   win32com.client.CDispatch
       The specified sheet object.
    """
    logging.debug(f'Opening sheet {sheet_name} in {workbook_name}')
    workbooks = []
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        # Get the currently open workbooks
        workbooks = excel.Workbooks
    except AttributeError as attr_err:
        logger.exception(attr_err)
        msg = f'Got an AttributeError while opening  {workbook_name} !{sheet_name}. Is the spreadsheet busy?'
        raise IOError(msg)
        # raise attr_err

    for workbook in workbooks:
        logger.debug(f"Found open Workbook: {workbook.Name}")
    logger.debug(f'Using {workbook_name} {sheet_name}')
    # Access a specific workbook by name
    try:
        if workbook_name not in [n.Name for n in workbooks]:
            ex_msg = f'No open workbook named: \'{workbook_name}\''
            raise IOError(ex_msg)
        workbook = workbooks[workbook_name]
    except com_error as ex:
        logger.error(f'Error opening {workbook_name}')
        if not workbooks:
            logger.error('No open workbooks')
        else:
            logger.info('Open workbooks: ')
            for wb in workbooks:
                logger.info(f'Found workbook {wb.Name}')
        raise ex
    # Now you can interact with the workbook, for example, read a cell value
    sheet = []
    try:
        if sheet_name not in [n.Name for n in workbook.Sheets]:
            ex_msg = f'{workbook_name} exists and is open, but there is no sheet named: \'{sheet_name}\''
            raise IOError(ex_msg)
        sheet = workbook.Sheets(sheet_name)
    except com_error as ex:
        logger.error(f'Error opening {sheet_name}')
        for s in workbook.Sheets:
            logger.error(f'Found sheet {s.Name}')
        raise ex
    return sheet
