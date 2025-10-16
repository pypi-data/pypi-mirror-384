import { createStore } from "solid-js/store";
import type { Component } from "solid-js";
import { For, createEffect, on, createMemo, onCleanup } from "solid-js";
import type { AppState, GraphNode, GraphLink, CanonicalPath } from "./types";
import { niceName, wrapText } from "./utils";
import * as d3 from "d3";
import styles from "./Graph.module.scss";
import { VIEWBOX_HEIGHT, VIEWBOX_WIDTH } from "./graph";

const LABEL_LINE_HEIGHT = 1.1; // em

const Graph: Component<{
  store: AppState;
  setApi: (api: { zoomToNode: (path: CanonicalPath) => void }) => void;
}> = props => {
  const [ui, setUi] = createStore(props.store.ui);
  // NOTE: `ui` creates a view, not a copy
  // https://docs.solidjs.com/concepts/stores#modifying-store-values
  let svgRef: SVGSVGElement | undefined;

  const handleClearSelection = () => {
    setUi("selectedNodeIndices", []);
  };

  createEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") handleClearSelection();
    };
    window.addEventListener("keydown", handleKeyDown);
    onCleanup(() => window.removeEventListener("keydown", handleKeyDown));
  });

  const selectedIndices = createMemo(
    () => new Set(props.store.ui.selectedNodeIndices)
  );

  /**
   * Computes the set of all links that should be visible when a node is
   * selected or highlighted.
   */
  const activeLinks = createMemo(() => {
    const selected = props.store.ui.selectedNodeIndices;
    const highlighted = props.store.ui.highlightedNodeIndex;
    const linkMap = props.store.linkMap;

    if (selected.length === 0 && highlighted === null) {
      return [];
    }

    const focusIndices = new Set(selected);
    if (highlighted !== null) {
      focusIndices.add(highlighted);
    }

    const linksToShow = new Set<GraphLink>();
    for (const index of focusIndices) {
      const links = linkMap.get(index);
      if (links) {
        for (const link of links) {
          linksToShow.add(link);
        }
      }
    }
    return [...linksToShow];
  });

  /**
   * Computes the set of all node indices that are part of the active
   * neighborhood (i.e., connected to a selected or highlighted node).
   */
  const activeNodeIndexSet = createMemo(() => {
    const selected = props.store.ui.selectedNodeIndices;
    const highlighted = props.store.ui.highlightedNodeIndex;
    const linkMap = props.store.linkMap;

    if (selected.length === 0 && highlighted === null) {
      return new Set<number>();
    }

    const focusIndices = new Set(selected);
    if (highlighted !== null) {
      focusIndices.add(highlighted);
    }

    const active = new Set(focusIndices);

    for (const index of focusIndices) {
      const links = linkMap.get(index);
      if (links) {
        for (const link of links) {
          active.add(link.source);
          active.add(link.target);
        }
      }
    }
    return active;
  });

  const isFocusActive = createMemo(
    () =>
      props.store.ui.selectedNodeIndices.length > 0 ||
      props.store.ui.highlightedNodeIndex !== null
  );

  const focusedNodeIndex = createMemo(() => {
    const highlightedIndex = ui.highlightedNodeIndex;
    if (highlightedIndex !== null) return highlightedIndex;

    const selectedIndices = ui.selectedNodeIndices;
    return selectedIndices.length === 1 ? selectedIndices[0] : null;
  });

  createEffect(
    on(
      () => props.store.nodes,
      nodes => {
        if (!svgRef) return;

        const zoom = d3
          .zoom<SVGSVGElement, unknown>()
          .scaleExtent([0.1, 10])
          .on("zoom", e => {
            const { k, x, y } = e.transform;
            setUi("view", { k, x, y });
          });

        const selection = d3.select(svgRef).call(zoom);

        props.setApi({
          zoomToNode: (targetPath: CanonicalPath) => {
            if (!svgRef) return;
            const targetNode = props.store.nodes.find(
              n => n.canonicalPath === targetPath
            );
            if (!targetNode) return;

            const { width, height } = svgRef.getBoundingClientRect();
            const { k } = ui.view;
            const targetScale = Math.min(
              8,
              Math.max(k, Math.min(width, height) / (targetNode.radius * 2.5))
            );

            const newTransform = d3.zoomIdentity
              .translate(width / 2, height / 2)
              .scale(targetScale)
              .translate(-targetNode.x, -targetNode.y);

            selection
              .transition()
              .duration(300)
              .ease(d3.easeCubic)
              .call(zoom.transform, newTransform);
          }
        });

        createEffect(() => {
          const { k, x, y } = ui.view;
          const transform = d3.zoomIdentity.translate(x, y).scale(k);
          const current = d3.zoomTransform(svgRef);
          if (current.k !== k || current.x !== x || current.y !== y) {
            selection.call(zoom.transform, transform);
          }
        });
      }
    )
  );

  const handleNodeClick = (nodeIndex: number, event: MouseEvent) => {
    event.stopPropagation();
    setUi("selectedNodeIndices", currentSelection => {
      const isAlreadySelected = currentSelection.includes(nodeIndex);
      if (event.shiftKey) {
        return isAlreadySelected
          ? currentSelection.filter(i => i !== nodeIndex)
          : [...currentSelection, nodeIndex];
      } else {
        return isAlreadySelected ? [] : [nodeIndex];
      }
    });
  };

  const nodeLabelWrapped = createMemo(() => {
    return props.store.nodes.map(node => {
      const lines = wrapText(niceName(node.canonicalPath));
      return {
        lines,
        startYOffset: -((lines.length - 1) * LABEL_LINE_HEIGHT) / 2
      };
    });
  });

  const isNodeLabelLegible = (node: GraphNode) => {
    const screenRadius = node.radius * props.store.ui.view.k;
    return screenRadius > 36 && screenRadius < 224;
  };

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
      preserveAspectRatio="xMidYMid meet"
      class={styles.graphSvg}
      onClick={e => e.target === svgRef && handleClearSelection()}
    >
      <GraphDefs />
      <g
        transform={`translate(${props.store.ui.view.x}, ${props.store.ui.view.y}) scale(${props.store.ui.view.k})`}
      >
        <g>
          <For each={activeLinks()}>
            {link => (
              <LinkPath
                link={link}
                focusedNodeIndex={focusedNodeIndex()}
                selectedIndices={selectedIndices()}
                nodes={props.store.nodes}
                k={props.store.ui.view.k}
              />
            )}
          </For>
        </g>
        <g>
          <For each={props.store.nodes}>
            {(node, i) => (
              <circle
                cx={node.x}
                cy={node.y}
                r={node.radius}
                fill={node.isGroup ? "transparent" : props.store.colorMap[i()]}
                stroke={node.isGroup ? props.store.colorMap[i()] : "none"}
                stroke-width={4 / ui.view.k}
                class={styles.node}
                classList={{
                  [styles.dimmed]:
                    isFocusActive() && !activeNodeIndexSet().has(i()),
                  [styles.selected]: selectedIndices().has(i())
                }}
                onClick={[handleNodeClick, i()]}
                onMouseEnter={() => setUi("highlightedNodeIndex", i())}
                onMouseLeave={() => setUi("highlightedNodeIndex", null)}
              />
            )}
          </For>
        </g>
        <g class={styles.labels}>
          <For each={nodeLabelWrapped()}>
            {(label, i) => {
              const node = props.store.nodes[i()];
              return (
                <text
                  x={node.x}
                  y={node.y}
                  font-size={Math.max(3, node.radius / 3)}
                  class={styles.nodeLabel}
                  classList={{
                    [styles.visible]: isFocusActive()
                      ? activeNodeIndexSet().has(i())
                      : isNodeLabelLegible(node)
                  }}
                >
                  <For each={label.lines}>
                    {(line, j) => (
                      <tspan
                        x={node.x}
                        dy={
                          j() === 0
                            ? `${label.startYOffset}em`
                            : `${LABEL_LINE_HEIGHT}em`
                        }
                      >
                        {line}
                      </tspan>
                    )}
                  </For>
                </text>
              );
            }}
          </For>
        </g>
      </g>
    </svg>
  );
};

const LinkPath: Component<{
  link: GraphLink;
  focusedNodeIndex: number | null;
  selectedIndices: Set<number>;
  nodes: GraphNode[];
  k: number;
}> = props => {
  const pathData = createMemo(() => getPath(props.link, props.nodes));

  const linkStyle = createMemo(() => {
    const { source: sourceIndex, target: targetIndex } = props.link;
    const focusedIndex = props.focusedNodeIndex;
    const selected = props.selectedIndices;

    const getStyleForIndex = (index: number) => {
      if (sourceIndex === index) {
        return {
          class: `${styles.link} ${styles.outgoing}`,
          marker: "url(#arrowhead-green)"
        };
      }
      if (targetIndex === index) {
        return {
          class: `${styles.link} ${styles.incoming}`,
          marker: "url(#arrowhead-blue)"
        };
      }
      return null;
    };

    if (focusedIndex !== null) {
      const style = getStyleForIndex(focusedIndex);
      if (style) return style;
    }

    for (const selectedIndex of selected) {
      const style = getStyleForIndex(selectedIndex);
      if (style) return style;
    }

    return { class: styles.link, marker: null };
  });

  return (
    <path
      d={pathData()}
      class={linkStyle().class}
      marker-mid={linkStyle().marker}
      stroke-width={3 / props.k}
    />
  );
};

const getPath = (link: GraphLink, nodes: GraphNode[]) => {
  const sourceNode = nodes[link.source];
  const targetNode = nodes[link.target];
  if (!sourceNode || !targetNode) return "";

  const dx = targetNode.x - sourceNode.x;
  const dy = targetNode.y - sourceNode.y;
  const dist = Math.hypot(dx, dy);
  if (dist < 1) return "";

  const sourceRadius = sourceNode.radius;
  const targetRadius = targetNode.radius;

  const sourceX = sourceNode.x + (dx * sourceRadius) / dist;
  const sourceY = sourceNode.y + (dy * sourceRadius) / dist;
  const targetX = targetNode.x - (dx * targetRadius) / dist;
  const targetY = targetNode.y - (dy * targetRadius) / dist;

  const midX = (sourceX + targetX) / 2;
  const midY = (sourceY + targetY) / 2;
  return `M ${sourceX},${sourceY} L ${midX},${midY} L ${targetX},${targetY}`;
};

const GraphDefs: Component = () => {
  return (
    <defs>
      <filter id="text-glow" x="-50%" y="-50%" width="200%" height="200%">
        <feFlood flood-color="black" result="glowColour" />
        <feComposite
          in="glowColour"
          in2="SourceAlpha"
          operator="in"
          result="colouredGlow"
        />
        <feGaussianBlur
          in="dilatedGlow"
          stdDeviation="1.5"
          result="blurredGlow"
        />
        <feMerge>
          <feMergeNode in="blurredGlow" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
      <marker
        id="arrowhead-green"
        viewBox="0 -5 10 10"
        refX="5"
        markerWidth="4"
        markerHeight="4"
        orient="auto-start-reverse"
      >
        <path d="M0,-5L10,0L0,5" fill="var(--accent-green)" />
      </marker>
      <marker
        id="arrowhead-blue"
        viewBox="0 -5 10 10"
        refX="5"
        markerWidth="4"
        markerHeight="4"
        orient="auto-start-reverse"
      >
        <path d="M0,-5L10,0L0,5" fill="var(--accent-blue)" />
      </marker>
    </defs>
  );
};

export default Graph;
