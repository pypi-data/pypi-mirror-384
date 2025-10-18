import {
  JupyterFrontEnd,
  type JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { shouldOpenFile, shouldOpenUntitledFile } from './handler';
import { NB_COMMANDS } from './constants';
import type { DocManagerFileEvent } from './models';
import { Contents } from '@jupyterlab/services';

const id = '@amzn/sagemaker-ui-doc-manager-jl-plugin:plugin';
const description = 'A JupyterLab extension for handling notebook documents.';

/**
 * Initialization for the sagemaker-ui-doc-manager-jl-plugin extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id,
  description,
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('sagemaker-ui-doc-manager-jl-plugin is activated!');

    window.addEventListener('message', async e => {
      const event = e.data as DocManagerFileEvent;
      if (shouldOpenFile(e)) {
        await app.commands.execute(NB_COMMANDS.OpenFileCommand, { path: event.payload.path });
        await app.commands.execute(NB_COMMANDS.ShowFileInBrowser);
      }
      if (shouldOpenUntitledFile(e)) {
          const { type, ext, path, content, format } = event.payload
          await app.serviceManager.contents.newUntitled({ type, ext, path }).then(async (model: Contents.IModel) => {
            if (content) {
              await app.serviceManager.contents.save(model.path, { type: model.type, content, format: format || 'text' })
            }
            await app.commands.execute(NB_COMMANDS.OpenFileCommand, { path: model.path });
            await app.commands.execute(NB_COMMANDS.ShowFileInBrowser);
          })
      }
    });
  }
};

export default plugin;
