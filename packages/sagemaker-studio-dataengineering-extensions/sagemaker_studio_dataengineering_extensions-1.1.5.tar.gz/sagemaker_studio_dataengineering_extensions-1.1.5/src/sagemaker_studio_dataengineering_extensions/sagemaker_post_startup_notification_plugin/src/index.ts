import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { PostStartupNotificationsService } from './services/PostStartupNotificationService'

/**
 * Initialization data for the sagemaker_post_startup_notification_plugin extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: '@amzn/sagemaker-post-startup-notification-plugin:plugin',
  description: 'A JupyterLab extension.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension sagemaker-post-startup-notification-plugin is activated!');
    app.restored.then(async () => {
      const service = new PostStartupNotificationsService();
      await service.initialize();
    });
  }
};

export default plugin;
