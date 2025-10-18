import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { IDisposable, DisposableDelegate } from '@lumino/disposable';

import { DocumentRegistry } from '@jupyterlab/docregistry';

import { PanelLayout } from '@lumino/widgets';
// import { ToolbarButton } from '@jupyterlab/apputils';
import {
  NotebookActions,
  NotebookPanel,
  INotebookModel
} from '@jupyterlab/notebook';

import '../style/index.css';

/**
 * Initialization data for the jupyterlab_exam_submission extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_exam_submission:plugin',
  description:
    'A button in JupyterLab to run the code cells and then to hide the code cells.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    app.docRegistry.addWidgetExtension('Notebook', new HideCodeExtension());
    console.log('JupyterLab extension jupyterlab_exam_submission_auto is activated!');
  }
};

export class HideCodeExtension
  implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel>
{
  createNew(
    panel: NotebookPanel,
    context: DocumentRegistry.IContext<INotebookModel>
  ): IDisposable {
    const hideTaggedCode = () => {
      console.log('Running all cells...');
     
      NotebookActions.runAll(panel.content, context.sessionContext);
      
      
        console.log('All cells executed. Hiding tagged code cells...');
        panel.content.widgets.forEach(cell => {
          console.log(cell)
          if (cell.model.type === 'code') {
            const tags = (cell.model.metadata['tags'] || []) as string[];
            if (Array.isArray(tags) && tags.includes('hide_code')) {
              const layout = cell.layout as PanelLayout;
              layout.widgets[1].hide();
            }

             if (Array.isArray(tags) && tags.includes('hide_output')) {
              const layout = cell.layout as PanelLayout;
              layout.widgets[3].hide();
            }
          }
        });
    };


    Promise.resolve(panel.context.sessionContext.ready).then(() => {
  console.log('Session ready. Hiding tagged code cells...');
  hideTaggedCode();
});

    // const buttonHideInput = new ToolbarButton({
    //   className: 'myButton',
    //   iconClass: 'fa fa-sm fa-graduation-cap fontawesome-colors',
    //   label: 'Initialize Exam',
    //   onClick: hideTaggedCode,
    //   tooltip: 'Hide Input'
    // });


    // panel.toolbar.insertItem(11, 'hideInput', buttonHideInput);

    return new DisposableDelegate(() => {
      // buttonHideInput.dispose();
    });
  }
}

export default plugin;