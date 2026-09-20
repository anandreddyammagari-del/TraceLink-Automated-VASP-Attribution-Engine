import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Shield, ExternalLink, AlertTriangle, Layers, Info, CheckCircle2 } from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';

const CATEGORY_COLORS = {
  SUSPECT_WALLET: '#DC2626',   // Alert Crimson
  INTERMEDIARY: '#334155',     // Slate Navy
  MIXER: '#7C3AED',            // Warning Violet
  BRIDGE: '#0284C7',           // Cyan
  VASP: '#166534'              // Verified Emerald
};

const CATEGORY_LABELS = {
  SUSPECT_WALLET: 'Suspect Root Wallet',
  INTERMEDIARY: 'Layering Intermediary',
  MIXER: 'Privacy Mixer / Tumbler',
  BRIDGE: 'Cross-Chain Bridge Contract',
  VASP: 'VASP / Exchange Deposit Cluster'
};

const TraceGraphD3 = ({ graphData, attribution, onSelectNode }) => {
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return;

    const width = 950;
    const height = 550;

    // Clear previous SVG contents
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('viewBox', [0, 0, width, height])
      .style('background-color', '#FFFFFF')
      .style('cursor', 'grab');

    // Container for zoom
    const container = svg.append('g');

    // Setup Zoom & Pan
    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Arrow marker definition
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#94A3B8');

    // Marker for VASP target
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead-vasp')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 26)
      .attr('refY', 0)
      .attr('markerWidth', 7)
      .attr('markerHeight', 7)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#166534');

    // Deep clone data for D3 mutation
    const nodes = graphData.nodes.map(d => ({ ...d }));
    const edges = graphData.edges.map(d => ({ ...d }));

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(140))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(45));

    // Draw Links
    const link = container.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(edges)
      .enter()
      .append('line')
      .attr('stroke', d => d.risk_flag === 'VASP_DEPOSIT' ? '#166534' : '#94A3B8')
      .attr('stroke-width', d => d.risk_flag === 'VASP_DEPOSIT' ? 3 : 2)
      .attr('stroke-dasharray', d => d.risk_flag === 'PEEL_CHAIN' ? '4,4' : 'none')
      .attr('marker-end', d => d.risk_flag === 'VASP_DEPOSIT' ? 'url(#arrowhead-vasp)' : 'url(#arrowhead)')
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        setSelectedEdge(d);
        setSelectedNode(null);
      });

    // Link value labels
    const linkText = container.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(edges)
      .enter()
      .append('text')
      .attr('font-size', '10px')
      .attr('font-family', 'JetBrains Mono')
      .attr('fill', '#475569')
      .attr('text-anchor', 'middle')
      .text(d => `${d.value} ${d.token_symbol || 'ETH'}`);

    // Draw Node Groups
    const node = container.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      )
      .on('click', (event, d) => {
        setSelectedNode(d);
        setSelectedEdge(null);
        if (onSelectNode) onSelectNode(d);
      });

    // Node outer halo for VASP or Suspect
    node.append('circle')
      .attr('r', d => d.category === 'VASP' ? 24 : (d.category === 'SUSPECT_WALLET' ? 22 : 16))
      .attr('fill', d => CATEGORY_COLORS[d.category] || '#64748B')
      .attr('fill-opacity', 0.15)
      .attr('stroke', d => CATEGORY_COLORS[d.category] || '#64748B')
      .attr('stroke-width', 2);

    // Node inner core
    node.append('circle')
      .attr('r', d => d.category === 'VASP' ? 18 : (d.category === 'SUSPECT_WALLET' ? 16 : 12))
      .attr('fill', d => CATEGORY_COLORS[d.category] || '#64748B')
      .attr('stroke', '#FFFFFF')
      .attr('stroke-width', 2);

    // Node Labels
    node.append('text')
      .attr('dy', 32)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', '#0F172A')
      .text(d => d.label || d.id.substring(0, 8));

    // Category sub-label
    node.append('text')
      .attr('dy', 44)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('fill', '#64748B')
      .text(d => d.category === 'VASP' ? 'TARGET VASP' : `Hop ${d.hop}`);

    // Simulation Tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      linkText
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2 - 5);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Auto-select suspect or VASP node by default
    const initialNode = nodes.find(n => n.category === 'VASP') || nodes[0];
    if (initialNode) setSelectedNode(initialNode);

    return () => simulation.stop();
  }, [graphData]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.25rem' }}>
      {/* Interactive SVG Canvas */}
      <div className="police-card" style={{ padding: '1rem', position: 'relative', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--police-navy-dark)' }}>
              Topological Fund Flow & Hop Attribution Canvas
            </span>
          </div>

          {/* Legend */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.7rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#DC2626' }}></span>
              Suspect
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#334155' }}></span>
              Intermediary
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#7C3AED' }}></span>
              Mixer
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#166534' }}></span>
              VASP
            </span>
          </div>
        </div>

        <svg ref={svgRef} style={{ width: '100%', height: '520px', border: '1px solid var(--border-light)', borderRadius: '4px' }} />
        <div style={{ position: 'absolute', bottom: '1.5rem', left: '1.5rem', fontSize: '0.7rem', color: '#64748B', background: 'rgba(255,255,255,0.85)', padding: '0.2rem 0.5rem', borderRadius: '3px' }}>
          Scroll to Zoom • Drag Nodes to Reposition • Click Node to Inspect
        </div>
      </div>

      {/* Forensic Inspector Sidebar */}
      <div className="police-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--police-navy-dark)', borderBottom: '1px solid var(--border-light)', paddingBottom: '0.5rem' }}>
          Forensic Entity Inspector
        </h3>

        {selectedNode ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8125rem' }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
                Entity Classification
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.15rem' }}>
                <span style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: CATEGORY_COLORS[selectedNode.category] || '#64748B'
                }}></span>
                <span style={{ fontWeight: 700, color: CATEGORY_COLORS[selectedNode.category] }}>
                  {CATEGORY_LABELS[selectedNode.category] || selectedNode.category}
                </span>
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
                Wallet Address / Identifier
              </span>
              <div className="font-mono" style={{ background: '#F1F5F9', padding: '0.35rem 0.5rem', borderRadius: '4px', wordBreak: 'break-all', fontSize: '0.75rem', marginTop: '0.15rem' }}>
                {selectedNode.id}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Hop Distance
                </span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-main)' }}>
                  Hop {selectedNode.hop}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Risk Score
                </span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: selectedNode.risk_score > 70 ? '#DC2626' : '#166534' }}>
                  {selectedNode.risk_score} / 100
                </div>
              </div>
            </div>

            {/* If VASP Node, show attribution specifics */}
            {selectedNode.category === 'VASP' && attribution && (
              <div style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', padding: '0.75rem', borderRadius: '6px', marginTop: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#166534' }}>
                    Attributed VASP Target
                  </span>
                  <ConfidenceBadge score={attribution.confidence_score} tier={attribution.confidence_tier} />
                </div>
                <div style={{ fontWeight: 700, color: '#0F2C59', fontSize: '0.875rem' }}>
                  {attribution.target_vasp_name}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#15803D', marginTop: '0.25rem' }}>
                  Inflow Volume: <strong>{attribution.total_volume} {attribution.token_symbol}</strong>
                </div>

                <div style={{ marginTop: '0.5rem', borderTop: '1px solid #DCFCE7', paddingTop: '0.5rem' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#166534', textTransform: 'uppercase' }}>
                    Statutory Evidence Factors
                  </span>
                  <ul style={{ paddingLeft: '1.2rem', marginTop: '0.25rem', fontSize: '0.72rem', color: '#1E3A8A' }}>
                    {attribution.evidence_breakdown?.map((factor, idx) => (
                      <li key={idx} style={{ marginBottom: '0.2rem' }}>{factor}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        ) : selectedEdge ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8125rem' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
              Transaction Edge Details
            </span>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>Hash:</span>
              <div className="font-mono" style={{ fontSize: '0.72rem', wordBreak: 'break-all', background: '#F1F5F9', padding: '0.3rem' }}>
                {selectedEdge.tx_hash}
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>Transferred:</span>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                {selectedEdge.value} {selectedEdge.token_symbol || 'ETH'}
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>Risk Flag:</span>
              <div>
                <span className="badge-amber" style={{ padding: '0.15rem 0.45rem', fontSize: '0.7rem', fontWeight: 700 }}>
                  {selectedEdge.risk_flag}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', textAlign: 'center', padding: '2rem 0' }}>
            Select any node or link on the canvas to inspect forensic properties.
          </div>
        )}
      </div>
    </div>
  );
};

export default TraceGraphD3;
