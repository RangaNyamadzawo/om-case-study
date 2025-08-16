import { ScaffolderEntitiesProcessor } from '@backstage/plugin-scaffolder-node';
import { createRouter } from '@backstage/plugin-scaffolder-backend';
import { myCustomAction } from './scaffolder/actions/customAction';

// ...inside the async function that builds the router:
const actions = [
  // other default actions...
  myCustomAction,
];

const router = await createRouter({
  // ...
  actions,
  // ...
});

return router;
