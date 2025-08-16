import { createTemplateAction } from '@backstage/plugin-scaffolder-node';
import { z } from 'zod';
import * as fs from 'fs/promises';
import * as path from 'path';

export const myCustomAction = createTemplateAction<{
  filename: string;
  contents: string;
}>({
  id: 'my:custom:action',
  description: 'Writes a file into the scaffolder temp workspace.',
  schema: {
    input: z.object({
      filename: z.string().describe('Relative path of the file to create'),
      contents: z.string().describe('File contents'),
    }),
    output: z
      .object({
        writtenPath: z.string(),
      })
      .partial(),
  },
  async handler(ctx) {
    const { filename, contents } = ctx.input;

    // The scaffolder provides a temporary workspace at ctx.workspacePath
    const target = path.resolve(ctx.workspacePath, filename);

    await fs.mkdir(path.dirname(target), { recursive: true });
    await fs.writeFile(target, contents, { encoding: 'utf8' });

    ctx.output('writtenPath', path.relative(ctx.workspacePath, target));
    ctx.logger.info(`Created ${target}`);
  },
});
