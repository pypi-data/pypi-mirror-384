import * as fs from "fs";
import { compileFromFile } from "json-schema-to-typescript";

const typeNames = [
  "activity",
  "actor",
  "collection",
  "object",
  "actor-header-info",
  "object-meta-info",
];

const filename = (name: string) => `src/${name}.d.ts`;

for (const name of typeNames) {
  compileFromFile(`../../docs/schemas/${name}.json`)
    .then((ts) => fs.writeFileSync(filename(name), ts))
    .catch((err) => console.error(err));
}

for (const name of typeNames) {
  console.log(`"./${name}": "./${filename(name)}",`);
}
