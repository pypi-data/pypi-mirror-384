#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class PortfolioMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'portfolio-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.portfolioData = null;
    this.loadPortfolioData();
    this.setupToolHandlers();
  }

  loadPortfolioData() {
    try {
      // Try multiple possible paths for the data file
      const possiblePaths = [
        process.env.DATA_PATH || '/app/db/sample-data.json',
        join(__dirname, '../db/sample-data.json'),
        join(__dirname, '../../db/sample-data.json'),
        './db/sample-data.json'
      ];
      
      let dataPath = null;
      for (const path of possiblePaths) {
        try {
          readFileSync(path, 'utf-8');
          dataPath = path;
          break;
        } catch (e) {
          // Continue to next path
        }
      }
      
      if (!dataPath) {
        throw new Error('No portfolio data file found in any expected location');
      }
      
      const rawData = readFileSync(dataPath, 'utf-8');
      this.portfolioData = JSON.parse(rawData);
      console.error(`Portfolio data loaded from: ${dataPath}`);
    } catch (error) {
      console.error('Failed to load portfolio data:', error);
      this.portfolioData = [];
    }
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_portfolio',
            description: 'Search through Srikanth\'s portfolio data by keywords, category, or content',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query to find relevant portfolio information'
                },
                category: {
                  type: 'string',
                  description: 'Filter by specific category (e.g., "Tech Stack", "Experience", "Education")'
                },
                limit: {
                  type: 'number',
                  description: 'Maximum number of results to return (default: 10)',
                  default: 10
                }
              },
              required: ['query']
            }
          },
          {
            name: 'get_portfolio_categories',
            description: 'Get all available categories in the portfolio data',
            inputSchema: {
              type: 'object',
              properties: {},
              additionalProperties: false
            }
          },
          {
            name: 'get_portfolio_item',
            description: 'Get a specific portfolio item by ID',
            inputSchema: {
              type: 'object',
              properties: {
                id: {
                  type: 'number',
                  description: 'The ID of the portfolio item to retrieve'
                }
              },
              required: ['id']
            }
          },
          {
            name: 'get_contact_info',
            description: 'Get all contact information for Srikanth',
            inputSchema: {
              type: 'object',
              properties: {},
              additionalProperties: false
            }
          },
          {
            name: 'get_tech_stack',
            description: 'Get detailed information about Srikanth\'s technical skills and tools',
            inputSchema: {
              type: 'object',
              properties: {
                type: {
                  type: 'string',
                  description: 'Filter by specific tech type (e.g., "Programming Languages", "Cloud Platforms")'
                }
              }
            }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'search_portfolio':
            return await this.searchPortfolio(args);
          case 'get_portfolio_categories':
            return await this.getPortfolioCategories();
          case 'get_portfolio_item':
            return await this.getPortfolioItem(args);
          case 'get_contact_info':
            return await this.getContactInfo();
          case 'get_tech_stack':
            return await this.getTechStack(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Error executing tool ${name}: ${error.message}`
        );
      }
    });
  }

  async searchPortfolio(args) {
    const { query, category, limit = 10 } = args;
    const searchTerm = query.toLowerCase();
    
    let results = this.portfolioData.filter(item => {
      // Filter by category if specified
      if (category && item.category.toLowerCase() !== category.toLowerCase()) {
        return false;
      }
      
      // Search in title, description, and keywords
      const searchableText = [
        item.title,
        item.description,
        ...item.keywords
      ].join(' ').toLowerCase();
      
      return searchableText.includes(searchTerm);
    });

    // Limit results
    results = results.slice(0, limit);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            query: query,
            category: category || 'all',
            resultsCount: results.length,
            results: results
          }, null, 2)
        }
      ]
    };
  }

  async getPortfolioCategories() {
    const categories = [...new Set(this.portfolioData.map(item => item.category))];
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            categories: categories,
            totalItems: this.portfolioData.length
          }, null, 2)
        }
      ]
    };
  }

  async getPortfolioItem(args) {
    const { id } = args;
    const item = this.portfolioData.find(item => item.id === id);
    
    if (!item) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Portfolio item with ID ${id} not found`
      );
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(item, null, 2)
        }
      ]
    };
  }

  async getContactInfo() {
    const contactItems = this.portfolioData.filter(item => item.category === 'Contact');
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            contact: contactItems
          }, null, 2)
        }
      ]
    };
  }

  async getTechStack(args) {
    const { type } = args;
    let techItems = this.portfolioData.filter(item => item.category === 'Tech Stack');
    
    if (type) {
      techItems = techItems.filter(item => 
        item.title.toLowerCase().includes(type.toLowerCase())
      );
    }
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            techStack: techItems,
            filterType: type || 'all'
          }, null, 2)
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Portfolio MCP server running on stdio');
  }
}

const server = new PortfolioMCPServer();
server.run().catch(console.error);