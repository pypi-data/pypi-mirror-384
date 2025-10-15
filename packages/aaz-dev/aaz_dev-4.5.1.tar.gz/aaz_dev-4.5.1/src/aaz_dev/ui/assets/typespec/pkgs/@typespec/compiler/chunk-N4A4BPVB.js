import {
  ResolveModuleError,
  resolveModule
} from "./chunk-D7SLJSYN.js";
import {
  NoTarget,
  SyntaxKind,
  compilerAssert,
  createDiagnostic,
  createDiagnosticCollector,
  createSourceFile,
  isImportStatement,
  parse
} from "./chunk-HK7BTPGC.js";
import {
  deepEquals,
  resolveTspMain
} from "./chunk-3K4NAOXV.js";
import {
  getDirectoryPath,
  joinPaths,
  resolvePath
} from "./chunk-OV76USRJ.js";

// src/typespec/core/packages/compiler/dist/src/utils/io.js
async function doIO(action, path, reportDiagnostic, options) {
  let result;
  try {
    result = await action(path);
  } catch (e) {
    let diagnostic;
    let target = options?.diagnosticTarget ?? NoTarget;
    if (e instanceof SyntaxError && options?.jsDiagnosticTarget) {
      target = options.jsDiagnosticTarget;
    }
    switch (e.code) {
      case "ENOENT":
        if (options?.allowFileNotFound) {
          return void 0;
        }
        diagnostic = createDiagnostic({ code: "file-not-found", target, format: { path } });
        break;
      default:
        diagnostic = createDiagnostic({
          code: "file-load",
          target,
          format: { message: e.message }
        });
        break;
    }
    reportDiagnostic(diagnostic);
    return void 0;
  }
  return result;
}
async function loadFile(host, path, load, reportDiagnostic, options) {
  const file = await doIO(host.readFile, path, reportDiagnostic, options);
  if (!file) {
    return [void 0, createSourceFile("", path)];
  }
  let data;
  try {
    data = load(file.text);
  } catch (e) {
    reportDiagnostic({
      code: "file-load",
      message: e.message,
      severity: "error",
      target: { file, pos: 1, end: 1 }
    });
    return [void 0, file];
  }
  return [data, file];
}
async function findProjectRoot(statFn, path) {
  let current = path;
  while (true) {
    const pkgPath = joinPaths(current, "package.json");
    const stat = await doIO(() => statFn(pkgPath), pkgPath, () => {
    });
    if (stat?.isFile()) {
      return current;
    }
    const parent = getDirectoryPath(current);
    if (parent === current) {
      return void 0;
    }
    current = parent;
  }
}

// src/typespec/core/packages/compiler/dist/src/core/entrypoint-resolution.js
async function resolveTypeSpecEntrypoint(host, path, reportDiagnostic) {
  const resolvedPath = resolvePath(path);
  const mainStat = await doIO(host.stat, resolvedPath, reportDiagnostic);
  if (!mainStat) {
    return void 0;
  }
  if (mainStat.isDirectory()) {
    return resolveTypeSpecEntrypointForDir(host, resolvedPath, reportDiagnostic);
  } else {
    return resolvedPath;
  }
}
async function resolveTypeSpecEntrypointForDir(host, dir, reportDiagnostic) {
  const pkgJsonPath = resolvePath(dir, "package.json");
  const [pkg] = await loadFile(host, pkgJsonPath, JSON.parse, reportDiagnostic, {
    allowFileNotFound: true
  });
  const tspMain = resolveTspMain(pkg);
  if (tspMain !== void 0) {
    return resolvePath(dir, tspMain);
  }
  return resolvePath(dir, "main.tsp");
}

// src/typespec/core/packages/compiler/dist/src/core/source-loader.js
async function createSourceLoader(host, options) {
  const diagnostics = createDiagnosticCollector();
  const tracer = options?.tracer;
  const seenSourceFiles = /* @__PURE__ */ new Set();
  const sourceFileLocationContexts = /* @__PURE__ */ new WeakMap();
  const sourceFiles = /* @__PURE__ */ new Map();
  const jsSourceFiles = /* @__PURE__ */ new Map();
  const loadedLibraries = /* @__PURE__ */ new Map();
  const externals = [];
  const externalsOpts = options?.externals;
  const isExternal = externalsOpts ? typeof externalsOpts === "function" ? externalsOpts : (x) => externalsOpts.includes(x) : () => false;
  async function importFile(path, diagnosticTarget, locationContext = { type: "project" }, kind = "import") {
    const sourceFileKind = host.getSourceFileKind(path);
    switch (sourceFileKind) {
      case "js":
        await importJsFile(path, locationContext, diagnosticTarget);
        break;
      case "typespec":
        await loadTypeSpecFile(path, locationContext, diagnosticTarget);
        break;
      default:
        diagnostics.add(createDiagnostic({
          code: kind === "import" ? "invalid-import" : "invalid-main",
          target: NoTarget
        }));
    }
  }
  return {
    importFile,
    importPath,
    resolution: {
      sourceFiles,
      jsSourceFiles,
      locationContexts: sourceFileLocationContexts,
      loadedLibraries,
      diagnostics: diagnostics.diagnostics,
      externals
    }
  };
  async function loadTypeSpecFile(path, locationContext, diagnosticTarget) {
    if (seenSourceFiles.has(path)) {
      return;
    }
    seenSourceFiles.add(path);
    const file = await doIO(host.readFile, path, (x) => diagnostics.add(x), {
      diagnosticTarget
    });
    if (file) {
      sourceFileLocationContexts.set(file, locationContext);
      await loadTypeSpecScript(file);
    }
  }
  async function loadTypeSpecScript(file) {
    if (sourceFiles.has(file.path)) {
      throw new RangeError("Duplicate script path: " + file.path);
    }
    const script = parseOrReuse(file);
    for (const diagnostic of script.parseDiagnostics) {
      diagnostics.add(diagnostic);
    }
    sourceFiles.set(file.path, script);
    await loadScriptImports(script);
    return script;
  }
  function parseOrReuse(file) {
    if (options?.getCachedScript) {
      const old = options.getCachedScript(file);
      if (old?.file === file && deepEquals(old.parseOptions, options.parseOptions)) {
        return old;
      }
    }
    const script = parse(file, options?.parseOptions);
    host.parseCache?.set(file, script);
    return script;
  }
  async function loadScriptImports(file) {
    const basedir = getDirectoryPath(file.file.path);
    await loadImports(file.statements.filter(isImportStatement).map((x) => ({ path: x.path.value, target: x })), basedir, getSourceFileLocationContext(file.file));
  }
  function getSourceFileLocationContext(sourcefile) {
    const locationContext = sourceFileLocationContexts.get(sourcefile);
    compilerAssert(locationContext, `SourceFile ${sourcefile.path} should have a declaration locationContext.`, { file: sourcefile, pos: 0, end: 0 });
    return locationContext;
  }
  async function loadImports(imports, relativeTo, locationContext) {
    for (const { path, target } of imports) {
      await importPath(path, target, relativeTo, locationContext);
    }
  }
  async function importPath(path, target, relativeTo, locationContext = { type: "project" }) {
    if (isExternal(path)) {
      externals.push(path);
      return;
    }
    const library = await resolveTypeSpecLibrary(path, relativeTo, target);
    if (library === void 0) {
      return;
    }
    if (library.type === "module") {
      loadedLibraries.set(library.manifest.name, {
        path: library.path,
        manifest: library.manifest
      });
      tracer?.trace("import-resolution.library", `Loading library "${path}" from "${library.mainFile}"`);
      const metadata = computeModuleMetadata(library);
      locationContext = {
        type: "library",
        metadata
      };
    }
    const importFilePath = library.type === "module" ? library.mainFile : library.path;
    const isDirectory = (await host.stat(importFilePath)).isDirectory();
    if (isDirectory) {
      await loadDirectory(importFilePath, locationContext, target);
      return;
    }
    return importFile(importFilePath, target, locationContext);
  }
  async function resolveTypeSpecLibrary(specifier, baseDir, target) {
    try {
      return await resolveModule(getResolveModuleHost(), specifier, {
        baseDir,
        directoryIndexFiles: ["main.tsp", "index.mjs", "index.js"],
        resolveMain(pkg) {
          return resolveTspMain(pkg) ?? pkg.main;
        },
        conditions: ["typespec"],
        fallbackOnMissingCondition: true
      });
    } catch (e) {
      if (e instanceof ResolveModuleError) {
        diagnostics.add(moduleResolutionErrorToDiagnostic(e, specifier, target));
        return void 0;
      } else {
        throw e;
      }
    }
  }
  async function loadDirectory(dir, locationContext, diagnosticTarget) {
    const mainFile = await resolveTypeSpecEntrypointForDir(host, dir, (x) => diagnostics.add(x));
    await loadTypeSpecFile(mainFile, locationContext, diagnosticTarget);
    return mainFile;
  }
  async function importJsFile(path, locationContext, diagnosticTarget) {
    const sourceFile = jsSourceFiles.get(path);
    if (sourceFile !== void 0) {
      return sourceFile;
    }
    const file = diagnostics.pipe(await loadJsFile(host, path, diagnosticTarget));
    if (file !== void 0) {
      sourceFileLocationContexts.set(file.file, locationContext);
      jsSourceFiles.set(path, file);
    }
    return file;
  }
  function getResolveModuleHost() {
    return {
      realpath: host.realpath,
      stat: host.stat,
      readFile: async (path) => {
        const file = await host.readFile(path);
        return file.text;
      }
    };
  }
}
function computeModuleMetadata(module) {
  const metadata = {
    type: "module",
    name: module.manifest.name
  };
  if (module.manifest.homepage) {
    metadata.homepage = module.manifest.homepage;
  }
  if (module.manifest.bugs?.url) {
    metadata.bugs = { url: module.manifest.bugs?.url };
  }
  if (module.manifest.version) {
    metadata.version = module.manifest.version;
  }
  return metadata;
}
async function loadJsFile(host, path, diagnosticTarget) {
  const file = createSourceFile("", path);
  const diagnostics = [];
  const exports = await doIO(host.getJsImport, path, (x) => {
    diagnostics.push(createDiagnostic({
      code: "js-error",
      format: { specifier: path, error: x.message },
      target: diagnosticTarget
    }));
  }, {
    diagnosticTarget,
    jsDiagnosticTarget: { file, pos: 0, end: 0 }
  });
  if (!exports) {
    return [void 0, diagnostics];
  }
  const node = {
    kind: SyntaxKind.JsSourceFile,
    id: {
      kind: SyntaxKind.Identifier,
      sv: "",
      pos: 0,
      end: 0,
      symbol: void 0,
      flags: 8
    },
    esmExports: exports,
    file,
    namespaceSymbols: [],
    symbol: void 0,
    pos: 0,
    end: 0,
    flags: 0
  };
  return [node, diagnostics];
}
function moduleResolutionErrorToDiagnostic(e, specifier, sourceTarget) {
  const target = e.pkgJson ? { file: createSourceFile(e.pkgJson.file.text, e.pkgJson.file.path), pos: 0, end: 0 } : sourceTarget;
  switch (e.code) {
    case "MODULE_NOT_FOUND":
      return createDiagnostic({ code: "import-not-found", format: { path: specifier }, target });
    case "INVALID_MODULE":
    case "INVALID_MODULE_EXPORT_TARGET":
      return createDiagnostic({
        code: "library-invalid",
        format: { path: specifier, message: e.message },
        target
      });
    case "INVALID_MAIN":
      return createDiagnostic({
        code: "library-invalid",
        format: { path: specifier, message: e.message },
        target
      });
    default:
      return createDiagnostic({ code: "import-not-found", format: { path: specifier }, target });
  }
}

export {
  doIO,
  loadFile,
  findProjectRoot,
  resolveTypeSpecEntrypoint,
  createSourceLoader,
  loadJsFile,
  moduleResolutionErrorToDiagnostic
};
