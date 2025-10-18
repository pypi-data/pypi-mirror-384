import {Cell, CodeCell, CodeCellModel} from '@jupyterlab/cells';
import {IOutput} from '@jupyterlab/nbformat';
import {NotebookPanel} from '@jupyterlab/notebook';
import {ReadonlyJSONObject} from '@lumino/coreutils';

import {DisplayData} from "../utils/types";
import {MIME_TYPES} from '../utils/constants';

export const useNotebookUpdater = (notebookPanel: NotebookPanel): ((code: DisplayData) => Promise<boolean>) => {
  async function findOutputLocation(interface_id: string): Promise<{ cell: Cell; outputIndex: number, mimeType: string } | undefined> {
    const cells = notebookPanel.content.widgets;

    // First check active cell for efficiency
    const activeCell = notebookPanel.content.activeCell;
    if (activeCell instanceof CodeCell) {
      const outputLocation = checkCellForOutput(activeCell, interface_id);
      if (outputLocation) return outputLocation;
    }

    for (const cell of cells) {
      if (cell instanceof CodeCell && cell !== activeCell) {
        const outputLocation = checkCellForOutput(cell, interface_id);
        if (outputLocation) return outputLocation;
      }
    }
    return undefined;
  }

  function checkCellForOutput(cell: CodeCell, interface_id: string) {
    const model = cell.model as CodeCellModel;
    const outputs = model.outputs;

    for (let outputIndex = 0; outputIndex < outputs.length; outputIndex++) {
      const output = outputs.get(outputIndex);

      for (let i = 0; i < MIME_TYPES.length; i++) {
        const mimeType = MIME_TYPES[i];
        const outputData = (output.toJSON().data as ReadonlyJSONObject)?.[mimeType] as unknown as DisplayData;
        if (outputData?.interface_id === interface_id) {
          return {cell, outputIndex, mimeType};
        }
      }
    }
    return undefined;
  }

  function createModifiedOutput(currentOutput: IOutput, newData: DisplayData, mimeType: string): IOutput {
    return {
      ...currentOutput,
      data: {
        [mimeType]: {
          ...newData
        }
      }
    };
  }

  return async (newData: DisplayData): Promise<boolean> => {
    try {
      await notebookPanel.context.ready;
      const location = await findOutputLocation(newData.interface_id);
      if (!location) {
        console.warn('Could not find matching output for interface_id:', newData.interface_id);
        return false;
      }

      const {cell, outputIndex, mimeType} = location;
      if (cell instanceof CodeCell) {
        const model = cell.model as CodeCellModel;
        const currentOutput = model.outputs.get(outputIndex);

        // Convert IOutputModel to IOutput using toJSON()
        const currentOutputData = currentOutput.toJSON();
        const modifiedOutput = createModifiedOutput(currentOutputData, newData, mimeType);

        model.outputs.set(outputIndex, modifiedOutput);
        model.isDirty = true;
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error updating SageMaker output:', error);
      return false;
    }
  }
}
