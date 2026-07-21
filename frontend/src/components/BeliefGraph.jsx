import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { xaiApi } from '../api/client'
import './BeliefGraph.css'

export default function BeliefGraph({ agentId, onSelectNode }) {
  const svgRef = useRef(null)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!agentId) return

    xaiApi.getAgentBeliefs(agentId)
      .then(res => {
        setData(res.data)
      })
      .catch(err => {
        setError(err.message)
      })
  }, [agentId])

  useEffect(() => {
    if (!data || !svgRef.current || data.beliefs.length === 0) return

    const width = 400
    const height = 300

    d3.select(svgRef.current).selectAll('*').remove()

    const nodes = [
      { id: agentId, type: 'agent', label: agentId.toUpperCase() },
      ...data.beliefs.map((b, i) => ({
        id: `belief-${i}`,
        type: b.source === 'verified' ? 'knowledge' : 'belief',
        label: b.fact,
      }))
    ]

    const links = data.beliefs.map((b, i) => ({
      source: agentId,
      target: `belief-${i}`,
      type: b.source,
    }))

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-150))
      .force('center', d3.forceCenter(width / 2, height / 2))

    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', d => d.type === 'verified' ? '#22c55e' : '#64748b')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', d => d.type === 'verified' ? '4,2' : 'none')

    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))

    node.append('circle')
      .attr('r', d => d.type === 'agent' ? 20 : 12)
      .attr('fill', d => {
        if (d.type === 'agent') return '#3b82f6'
        if (d.type === 'knowledge') return '#22c55e'
        return '#f59e0b'
      })
      .style('cursor', 'pointer')
      .on('click', (event, d) => onSelectNode && onSelectNode(d))

    node.append('text')
      .text(d => d.type === 'agent' ? d.label : d.label.substring(0, 15))
      .attr('x', 15)
      .attr('y', 5)
      .attr('font-size', '10px')
      .attr('fill', '#e2e8f0')

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    return () => simulation.stop()
  }, [data, agentId, onSelectNode])

  if (error) return <div className="belief-graph-error">{error}</div>
  if (!data || data.beliefs.length === 0) {
    return (
      <div className="belief-graph-empty">
        <p>No beliefs recorded for {agentId}</p>
        <small>Beliefs appear as agents make decisions</small>
      </div>
    )
  }

  return (
    <div className="belief-graph">
      <h3>Belief Graph: {agentId.toUpperCase()}</h3>
      <svg ref={svgRef}></svg>
      <div className="belief-legend">
        <span className="legend-item"><span className="dot agent"></span>Agent</span>
        <span className="legend-item"><span className="dot belief"></span>Belief</span>
        <span className="legend-item"><span className="dot knowledge"></span>Verified Knowledge</span>
      </div>
    </div>
  )
}