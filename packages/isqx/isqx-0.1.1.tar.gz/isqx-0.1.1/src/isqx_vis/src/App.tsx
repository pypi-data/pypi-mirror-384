import type { Component } from "solid-js";
import {
  createSignal,
  Show,
  onMount,
  onCleanup,
  createMemo,
  createEffect,
  createResource
} from "solid-js";
import { createStore } from "solid-js/store";
import type { IsqxData, AppState, CanonicalPath } from "./types";
import { processGraphData } from "./graph";
import Graph from "./Graph";
import Panel from "./Panel";
import { JumpContext } from "./JumpContext";
import { resizable } from "./resize";
import styles from "./App.module.scss";

const LOCALSTORAGE_KEY = "isqx-vis-data";

const App: Component = () => {
  const [store, setStore] = createStore<AppState>({
    data: null,
    nodes: [],
    links: [],
    linkMap: new Map(),
    colorMap: [],
    ui: {
      selectedNodeIndices: [],
      highlightedNodeIndex: null,
      view: { k: 1, x: 0, y: 0 }
    }
  });
  const [panelSize, setSidePanelSize] = createSignal(350);
  const [isMobile, setIsMobile] = createSignal(window.innerWidth <= 768);

  const [dataSource, setDataSource] = createSignal<string | File | IsqxData>();
  const fetchData = async (
    source: string | File | IsqxData
  ): Promise<IsqxData> => {
    if (typeof source !== "string" && !(source instanceof File)) {
      return source;
    }
    let jsonString: string;
    if (typeof source === "string") {
      const response = await fetch(source);
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      jsonString = await response.text();
    } else {
      jsonString = await source.text();
    }
    const data = JSON.parse(jsonString);
    localStorage.setItem(LOCALSTORAGE_KEY, jsonString);
    return data;
  };
  const [rawData] = createResource(dataSource, fetchData);
  const handleFileLoad = (file: File) => setDataSource(file);
  const handleUrlLoad = (url: string) => setDataSource(url);

  onMount(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    onCleanup(() => window.removeEventListener("resize", handleResize));

    const urlParams = new URLSearchParams(window.location.search);
    const autoLoad = urlParams.has("autoLoad");
    const storedData = localStorage.getItem(LOCALSTORAGE_KEY);

    if (autoLoad) {
      handleUrlLoad("assets/objects.json");
    } else if (storedData) {
      try {
        setDataSource(JSON.parse(storedData) as IsqxData);
      } catch (e) {
        console.error("failed to parse data from localStorage", e);
        localStorage.removeItem(LOCALSTORAGE_KEY);
      }
    }

    const syncFromURL = () => {
      const map = pathToIndexMap();
      if (map.size === 0) return;

      const urlParams = new URLSearchParams(window.location.search);
      const selectedPaths =
        urlParams.get("selected")?.split(",").filter(Boolean) ?? [];
      const indices: number[] = [];
      const malformedPaths: string[] = [];

      for (const path of selectedPaths) {
        const index = map.get(path);
        if (index !== undefined) {
          indices.push(index);
        } else {
          malformedPaths.push(path);
        }
      }
      if (malformedPaths.length > 0) {
        alert(
          `could not find the following quantities: ${malformedPaths.join(", ")}`
        );
      }

      const currentIndices = store.ui.selectedNodeIndices;
      const isOutOfSync =
        indices.length !== currentIndices.length ||
        !indices.every(i => currentIndices.includes(i));

      if (isOutOfSync) {
        setStore("ui", "selectedNodeIndices", indices);
      }
    };

    window.addEventListener("popstate", syncFromURL);
    onCleanup(() => window.removeEventListener("popstate", syncFromURL));
  });

  createEffect(() => {
    const data = rawData();
    if (!data) {
      setStore("data", null);
      return;
    }
    setStore("data", data.qtyKinds);
    if (!data) return;
    const { nodes, links, linkMap } = processGraphData(data.qtyKinds);
    const numNodes = nodes.length || 1;
    const colorMap = nodes.map((_, i) => {
      const hue = (i / numNodes) * 360 * 0.7;
      return `oklch(0.5498 0.0934 ${hue})`; // darker: 0.4216 0.0715
    });
    setStore({ nodes, links, linkMap, colorMap });

    const map = new Map(nodes.map((n, i) => [n.canonicalPath, i]));
    const urlParams = new URLSearchParams(window.location.search);
    const selectedPaths =
      urlParams.get("selected")?.split(",").filter(Boolean) ?? [];

    if (selectedPaths.length > 0) {
      const indices = selectedPaths
        .map(path => map.get(path))
        .filter((index): index is number => index !== undefined);
      setStore("ui", "selectedNodeIndices", indices);
    }
  });
  const clearData = () => {
    localStorage.removeItem(LOCALSTORAGE_KEY);
    setStore("data", null);
    history.pushState({}, "", window.location.pathname);
  };

  let graphApi: { zoomToNode: (path: CanonicalPath) => void };

  const pathToIndexMap = createMemo(
    () => new Map(store.nodes.map((n, i) => [n.canonicalPath, i]))
  );

  createEffect(() => {
    const paths = store.ui.selectedNodeIndices
      .map(index => store.nodes[index]?.canonicalPath)
      .filter(Boolean);

    const url = new URL(window.location.href);
    const currentPaths = url.searchParams.get("selected")?.split(",") ?? [];

    const isOutOfSync =
      paths.length !== currentPaths.length ||
      !paths.every(p => currentPaths.includes(p));

    if (isOutOfSync) {
      if (paths.length > 0) {
        url.searchParams.set("selected", paths.join(","));
      } else {
        url.searchParams.delete("selected");
      }
      history.pushState({}, "", url);
    }
  });

  const jumpToNode = (path: CanonicalPath) => {
    const index = pathToIndexMap().get(path);
    if (index !== undefined) {
      setStore("ui", "selectedNodeIndices", [index]);
      setStore("ui", "highlightedNodeIndex", index);
      graphApi?.zoomToNode(path);
    }
  };

  const mainLayoutStyle = createMemo(() => {
    const size = `${panelSize()}px`;
    return isMobile()
      ? { "grid-template-rows": `1fr ${size}` }
      : { "grid-template-columns": `${size} 1fr` };
  });

  return (
    <div class={styles.app}>
      <Show
        when={store.data}
        fallback={
          <SplashContainer
            onFileLoad={handleFileLoad}
            onUrlLoad={handleUrlLoad}
            error={rawData.error}
          />
        }
      >
        {_ => (
          <JumpContext.Provider value={jumpToNode}>
            <div
              class={styles.mainLayout}
              classList={{ [styles.mobile]: isMobile() }}
              style={mainLayoutStyle()}
            >
              <aside class={styles.panel}>
                <Panel store={store} onClearData={clearData} />
              </aside>
              <main class={styles.svgContainer}>
                <Graph store={store} setApi={api => (graphApi = api)} />
              </main>
              <div
                class={styles.resizer}
                style={
                  isMobile()
                    ? { top: `calc(100% - ${panelSize()}px)` }
                    : { left: `${panelSize()}px` }
                }
                use:resizable={{
                  isMobile,
                  size: panelSize,
                  onSizeChange: setSidePanelSize,
                  minSize: 50
                }}
              />
            </div>
          </JumpContext.Provider>
        )}
      </Show>
    </div>
  );
};

const DEFAULT_OBJECTS_URL = "assets/objects.json";

const SplashContainer: Component<{
  onFileLoad: (file: File) => void;
  onUrlLoad: (url: string) => void;
  error?: Error;
}> = props => {
  const [isFileDragging, setIsFileDragging] = createSignal(false);
  const [urlInput, setUrlInput] = createSignal(DEFAULT_OBJECTS_URL);
  let fileInputRef: HTMLInputElement | undefined;

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsFileDragging(false);
    const file = e.dataTransfer?.files[0];
    if (file) props.onFileLoad(file);
  };

  const handleFileChange = (e: Event) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) props.onFileLoad(file);
  };

  const handleUrlButtonClick = () => {
    if (urlInput()) props.onUrlLoad(urlInput());
  };

  return (
    <div class={styles.splashContainer}>
      <div
        class={styles.dropZone}
        classList={{ [styles.active]: isFileDragging() }}
        onClick={() => fileInputRef?.click()}
        onDrop={handleDrop}
        onDragOver={e => {
          e.preventDefault();
          setIsFileDragging(true);
        }}
        onDragLeave={e => {
          e.preventDefault();
          setIsFileDragging(false);
        }}
      >
        <input
          type="file"
          accept=".json"
          ref={fileInputRef}
          onChange={handleFileChange}
        />
        <h2>
          select or drop <code>objects.json</code>
        </h2>
      </div>
      <div class={styles.urlLoader}>
        <p>or load from a URL:</p>
        <input
          type="text"
          value={urlInput()}
          onInput={e => setUrlInput(e.currentTarget.value)}
          onKeyPress={e => e.key === "Enter" && handleUrlButtonClick()}
          aria-label="url to objects.json"
        />
        <button onClick={handleUrlButtonClick}>Load</button>
        <Show when={props.error}>
          <p style={{ color: "red", "margin-top": "1rem" }}>
            failed to load data: {props.error!.message}
          </p>
        </Show>
      </div>
    </div>
  );
};

export default App;
