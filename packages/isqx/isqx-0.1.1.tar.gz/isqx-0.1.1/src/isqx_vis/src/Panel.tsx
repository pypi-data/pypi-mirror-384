import type { Component, ParentComponent } from "solid-js";
import { createStore } from "solid-js/store";
import { For, Show, createMemo, lazy } from "solid-js";
import type {
  AppState,
  GraphNode,
  StrFragment,
  SymbolDetail,
  EquationDetail,
  WikidataDetail,
  CanonicalPath
} from "./types";
import { niceName, findCanonicalPathInDescription } from "./utils";
import styles from "./Panel.module.scss";
import { useJumper } from "./JumpContext";

const KaTeX = lazy(() => import("./KaTeX"));

const CrossRef: ParentComponent<{
  targetPath: CanonicalPath;
}> = props => {
  const jumpToNode = useJumper();
  const handleClick = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    jumpToNode!(props.targetPath);
  };

  return (
    <a href="#" onClick={handleClick}>
      {props.children}
    </a>
  );
};

function isAnchor(
  fragment: StrFragment
): fragment is { text: string; path: string } {
  return (
    typeof fragment === "object" && fragment !== null && "path" in fragment
  );
}

const RenderFragment: Component<{
  fragment: StrFragment;
  noLinks?: boolean;
}> = props => {
  const fragment = () => props.fragment;

  return (
    <Show
      when={isAnchor(fragment()) && !props.noLinks}
      fallback={
        <>
          {isAnchor(fragment())
            ? (fragment() as { text: string }).text
            : fragment()}
        </>
      }
    >
      <CrossRef targetPath={(fragment() as { path: string }).path}>
        {(fragment() as { text: string }).text}
      </CrossRef>
    </Show>
  );
};

const RenderFragments: Component<{
  fragments: StrFragment | StrFragment[];
  noLinks?: boolean;
}> = props => {
  const fragments = () =>
    Array.isArray(props.fragments) ? props.fragments : [props.fragments];
  return (
    <For each={fragments()}>
      {fragment => (
        <RenderFragment fragment={fragment} noLinks={props.noLinks} />
      )}
    </For>
  );
};

const Symbol: Component<{ symbol: SymbolDetail }> = props => (
  <>
    <KaTeX text={props.symbol.katex} />
    <Show when={props.symbol.remarks}>
      <span class={styles.symbolRemarks}> ({props.symbol.remarks})</span>
    </Show>
  </>
);

const EquationsSection: Component<{
  equations: EquationDetail[] | undefined;
}> = props => (
  <Show when={props.equations && props.equations.length > 0}>
    <div class={styles.detailSection}>
      <h4 style={{ color: "var(--accent-green)" }}>Equations</h4>
      <For each={props.equations}>
        {eq => (
          <div class={styles.equationBlock}>
            <KaTeX text={eq.katex} display={true} />
            <Show when={eq.where}>
              <div class={styles.whereClause}>
                <For each={eq.where}>
                  {w => (
                    <div class={styles.whereRow}>
                      <span class={styles.whereSymbol}>
                        <KaTeX text={w.symbol} />
                      </span>
                      <span>=</span>
                      <span>
                        <RenderFragments fragments={w.description} />
                        <Show when={w.unit}>
                          <>
                            {" ("}
                            <RenderFragments fragments={w.unit!} noLinks />
                            {")"}
                          </>
                        </Show>
                      </span>
                    </div>
                  )}
                </For>
              </div>
            </Show>
          </div>
        )}
      </For>
    </div>
  </Show>
);

const IncomingLinksSection: Component<{
  node: GraphNode;
  index: number;
  store: AppState;
}> = props => {
  const hydratedLinks = createMemo(() => {
    const links = props.store.linkMap.get(props.index) ?? [];
    return links
      .map(link => {
        if (link.source === props.index) return null; // only incoming
        const sourceNode = props.store.nodes[link.source];
        if (!sourceNode) return null;

        const relevantEquations =
          sourceNode.details.equations?.filter(eq =>
            eq.where?.some(
              clause =>
                findCanonicalPathInDescription(clause.description) ===
                props.node.canonicalPath
            )
          ) ?? [];

        return {
          sourceNode,
          sourceIndex: link.source,
          equations: relevantEquations
        };
      })
      .filter(Boolean) as {
      sourceNode: GraphNode;
      sourceIndex: number;
      equations: EquationDetail[];
    }[];
  });

  return (
    <Show when={hydratedLinks().length > 0}>
      <div class={styles.detailSection}>
        <h4 style={{ color: "var(--accent-blue)" }}>Referenced by</h4>
        <div class={styles.definedIn}>
          <For each={hydratedLinks()}>
            {({ sourceNode, sourceIndex, equations }) => (
              <div
                class={styles.definedInDetail}
                style={{
                  "border-left-color": props.store.colorMap[sourceIndex]
                }}
              >
                <CrossRef targetPath={sourceNode.canonicalPath}>
                  {niceName(sourceNode.canonicalPath)}
                </CrossRef>
                <For each={equations}>
                  {eq => (
                    <div class={styles.equationBlock}>
                      <KaTeX text={eq.katex} display={true} />
                    </div>
                  )}
                </For>
              </div>
            )}
          </For>
        </div>
      </div>
    </Show>
  );
};

const WikidataSection: Component<{
  wikidata: WikidataDetail[] | undefined;
}> = props => (
  <Show when={props.wikidata && props.wikidata.length > 0}>
    <div class={styles.detailSection}>
      <h4>Wikidata</h4>
      <For each={props.wikidata}>
        {(wd, i) => (
          <>
            <a
              href={`https://www.wikidata.org/wiki/${wd.qcode}`}
              target="_blank"
              rel="noopener"
            >
              {wd.qcode}
            </a>
            {i() < props.wikidata!.length - 1 ? " " : ""}
          </>
        )}
      </For>
    </div>
  </Show>
);

const NodeDetail: Component<{
  node: GraphNode;
  index: number;
  store: AppState;
  isExpanded: boolean;
  onToggle: () => void;
}> = props => {
  const details = () => props.node.details;
  const color = () => props.store.colorMap[props.index];

  return (
    <div class={styles.nodeDetail} style={{ "border-left-color": color() }}>
      <div class={styles.nodeHeader}>
        <h3 onClick={props.onToggle}>{niceName(props.node.canonicalPath)}</h3>
        <div class={styles.symbols}>
          <For each={details().symbols}>
            {(symbol, i) => (
              <>
                <Symbol symbol={symbol} />
                {i() < details().symbols!.length - 1 ? ", " : ""}
              </>
            )}
          </For>
        </div>
      </div>
      <Show when={props.isExpanded}>
        <EquationsSection equations={details().equations} />
        <IncomingLinksSection
          node={props.node}
          index={props.index}
          store={props.store}
        />
        <WikidataSection wikidata={details().wikidata} />
      </Show>
    </div>
  );
};

const Panel: Component<{
  store: AppState;
  onClearData: () => void;
}> = props => {
  const [expandedState, setExpandedState] = createStore<{
    [key: number]: boolean;
  }>({});

  const nodesToDisplay = createMemo(() => {
    const selected = props.store.ui.selectedNodeIndices;
    const highlighted = props.store.ui.highlightedNodeIndex;
    const allNodes = props.store.nodes;

    const orderedIndices = [...selected];
    if (highlighted !== null && !selected.includes(highlighted)) {
      orderedIndices.push(highlighted);
    }

    return orderedIndices.map(index => ({
      node: allNodes[index],
      index
    }));
  });

  const handleToggle = (index: number) => {
    const isCurrentlyExpanded = expandedState[index] ?? true;
    setExpandedState(index, !isCurrentlyExpanded);
  };

  const collapseAll = () => {
    const update: { [key: number]: boolean } = {};
    for (const { index } of nodesToDisplay()) {
      update[index] = false;
    }
    setExpandedState(update);
  };

  const showAll = () => {
    const update: { [key: number]: boolean } = {};
    for (const { index } of nodesToDisplay()) {
      update[index] = true;
    }
    setExpandedState(update);
  };

  const isExpanded = (index: number) => expandedState[index] ?? true;

  return (
    <>
      <div class={styles.controls}>
        <button onClick={props.onClearData}>Clear Data</button>
        <Show when={nodesToDisplay().length > 0}>
          <button onClick={collapseAll}>Collapse All</button>
          <button onClick={showAll}>Show All</button>
        </Show>
      </div>
      <div class={styles.nodeDetails}>
        <For each={nodesToDisplay()}>
          {({ node, index }) => (
            <>
              <Show
                when={
                  index === props.store.ui.highlightedNodeIndex &&
                  props.store.ui.selectedNodeIndices.length > 0 &&
                  !props.store.ui.selectedNodeIndices.includes(index)
                }
              >
                <hr class={styles.separator} />
              </Show>
              <NodeDetail
                node={node}
                index={index}
                store={props.store}
                isExpanded={isExpanded(index)}
                onToggle={() => handleToggle(index)}
              />
            </>
          )}
        </For>
      </div>
    </>
  );
};

export default Panel;
