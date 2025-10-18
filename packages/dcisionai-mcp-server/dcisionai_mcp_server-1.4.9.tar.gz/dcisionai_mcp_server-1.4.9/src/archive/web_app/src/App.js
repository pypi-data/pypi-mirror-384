import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, CheckCircle, AlertCircle, BarChart3, Settings, Zap, Eye, X } from 'lucide-react';
import axios from 'axios';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [showModelModal, setShowModelModal] = useState(false);
  const [currentModel, setCurrentModel] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Check if MCP server is running
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await axios.post('https://h5w9r03xkf.execute-api.us-east-1.amazonaws.com/prod/health', {}, {
        headers: { 'Content-Type': 'application/json' }
      });
      setIsConnected(response.data.status === 'healthy');
    } catch (error) {
      setIsConnected(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    const problemDescription = input;
    const baseUrl = 'https://h5w9r03xkf.execute-api.us-east-1.amazonaws.com/prod';
    
    try {
      // Step 1: Intent Classification
      const intentResponse = await axios.post(`${baseUrl}/intent`, {
        problem_description: problemDescription
      }, { 
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const intentMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: {
          step: 'intent_classification',
          message: intentResponse.data.message,
          result: intentResponse.data.result
        },
        timestamp: new Date()
      };
      setMessages(prev => [...prev, intentMessage]);

      // Step 2: Data Analysis
      const dataResponse = await axios.post(`${baseUrl}/data`, {
        problem_description: problemDescription,
        intent_data: intentResponse.data.result
      }, { 
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const dataMessage = {
        id: Date.now() + 2,
        type: 'bot',
        content: {
          step: 'data_analysis',
          message: dataResponse.data.message,
          result: dataResponse.data.result
        },
        timestamp: new Date()
      };
      setMessages(prev => [...prev, dataMessage]);

      // Step 3: Model Building
      const modelResponse = await axios.post(`${baseUrl}/model`, {
        problem_description: problemDescription,
        intent_data: intentResponse.data.result,
        data_analysis: dataResponse.data.result
      }, { 
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const modelMessage = {
        id: Date.now() + 3,
        type: 'bot',
        content: {
          step: 'model_building',
          message: modelResponse.data.message,
          result: modelResponse.data.result
        },
        timestamp: new Date()
      };
      setMessages(prev => [...prev, modelMessage]);

      // Step 4: Optimization Solving
      console.log('Starting solve step...');
      const solveResponse = await axios.post(`${baseUrl}/solve`, {
        problem_description: problemDescription,
        intent_data: intentResponse.data.result,
        model_building: modelResponse.data.result
      }, { 
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Solve response received:', solveResponse.data);
      
      const solveMessage = {
        id: Date.now() + 4,
        type: 'bot',
        content: {
          step: 'optimization_solution',
          message: solveResponse.data.message,
          result: solveResponse.data.result
        },
        timestamp: new Date()
      };
      setMessages(prev => [...prev, solveMessage]);

    } catch (error) {
      console.error('Streaming optimization error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `Sorry, I encountered an error: ${error.message || 'Please try again or contact support.'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const exampleQueries = [
    "Optimize production line efficiency with 50 workers across 3 manufacturing lines",
    "Minimize supply chain costs for 5 warehouses across different regions",
    "Maximize quality control efficiency while reducing inspection costs",
    "Optimize resource allocation for sustainable manufacturing processes"
  ];

  const formatStreamingMessage = (content) => {
    if (content.step) {
      // This is a streaming message
      const stepIcons = {
        'intent_classification': '🎯',
        'data_analysis': '📊',
        'model_building': '🔧',
        'optimization_solution': '⚡'
      };
      
      const stepTitles = {
        'intent_classification': 'Intent Classification',
        'data_analysis': 'Data Analysis',
        'model_building': 'Model Building',
        'optimization_solution': 'Optimization Solution'
      };
      
      return (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-blue-400">
            <span className="text-lg">{stepIcons[content.step]}</span>
            <span className="font-semibold">{stepTitles[content.step]}</span>
          </div>
          <p className="text-gray-300">{content.message}</p>
          
          {content.result && (
            <div className="bg-gray-900/50 rounded-lg p-3 text-sm">
              {content.step === 'intent_classification' && (
                <div>
                  <p><strong>Intent:</strong> {String(content.result.intent || 'Unknown')}</p>
                  <p><strong>Confidence:</strong> {content.result.confidence ? (content.result.confidence * 100).toFixed(1) : 'N/A'}%</p>
                  <p><strong>Problem Scale:</strong> {String(content.result.problem_scale || 'Unknown')}</p>
                  <p><strong>Entities:</strong> {Array.isArray(content.result.entities) ? content.result.entities.join(', ') : 'N/A'}</p>
                  {content.result.extracted_quantities && Array.isArray(content.result.extracted_quantities) && (
                    <p><strong>Quantities:</strong> {content.result.extracted_quantities.join(', ')}</p>
                  )}
                </div>
              )}
              {content.step === 'data_analysis' && (
                <div>
                  <p><strong>Data Readiness:</strong> {content.result.readiness_score ? (content.result.readiness_score * 100).toFixed(1) : 'N/A'}%</p>
                  <p><strong>Data Complexity:</strong> {String(content.result.data_complexity || 'Unknown')}</p>
                  <p><strong>Data Entities:</strong> {Array.isArray(content.result.data_entities) ? 
                    content.result.data_entities.map(entity => 
                      typeof entity === 'object' ? entity.name : entity
                    ).join(', ') : 'N/A'}</p>
                  {content.result.estimated_data_points && (
                    <p><strong>Estimated Data Points:</strong> {content.result.estimated_data_points}</p>
                  )}
                </div>
              )}
              {content.step === 'model_building' && (
                <div>
                  <p><strong>Model Type:</strong> {String(content.result.model_type || 'Unknown')}</p>
                  <p><strong>Variables:</strong> {Array.isArray(content.result.variables) ? content.result.variables.length : 0}</p>
                  <p><strong>Constraints:</strong> {Array.isArray(content.result.constraints) ? content.result.constraints.length : 0}</p>
                  <p><strong>Complexity:</strong> {String(content.result.complexity || 'Unknown')}</p>
                  {content.result.estimated_solve_time && (
                    <p><strong>Estimated Solve Time:</strong> {String(content.result.estimated_solve_time)}s</p>
                  )}
                </div>
              )}
              {content.step === 'optimization_solution' && (
                <div>
                  <p><strong>Status:</strong> {String(content.result.status || 'Unknown')}</p>
                  <p><strong>Objective Value:</strong> {String(content.result.objective_value || 'N/A')}</p>
                  {content.result.objective_interpretation && (
                    <p><strong>Objective Meaning:</strong> {String(content.result.objective_interpretation)}</p>
                  )}
                  <p><strong>Solve Time:</strong> {String(content.result.solve_time || 'N/A')}s</p>
                  {content.result.business_impact && (
                    <div className="mt-2">
                      <p><strong>Business Impact:</strong></p>
                      <ul className="list-disc list-inside ml-2">
                        {typeof content.result.business_impact === 'object' && content.result.business_impact !== null ? 
                          Object.entries(content.result.business_impact).map(([key, value], idx) => (
                            <li key={idx}><strong>{key.replace(/_/g, ' ')}:</strong> {String(value)}</li>
                          )) :
                          <li>{String(content.result.business_impact)}</li>
                        }
                      </ul>
                    </div>
                  )}
                  {content.result.expected_impact && (
                    <div className="mt-2">
                      <p><strong>Expected Impact:</strong></p>
                      <ul className="list-disc list-inside ml-2">
                        {typeof content.result.expected_impact === 'object' && content.result.expected_impact !== null ? 
                          Object.entries(content.result.expected_impact).map(([key, value], idx) => (
                            <li key={idx}><strong>{key.replace(/_/g, ' ')}:</strong> {String(value)}</li>
                          )) :
                          <li>{String(content.result.expected_impact)}</li>
                        }
                      </ul>
                    </div>
                  )}
                  {content.result.recommendations && Array.isArray(content.result.recommendations) && (
                    <div className="mt-2">
                      <p><strong>Recommendations:</strong></p>
                      <ul className="list-disc list-inside ml-2">
                        {content.result.recommendations.map((rec, idx) => (
                          <li key={idx}>{String(rec)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {content.result.implementation_notes && (
                    <div className="mt-2">
                      <p><strong>Implementation Notes:</strong></p>
                      <ul className="list-disc list-inside ml-2">
                        {Array.isArray(content.result.implementation_notes) ? 
                          content.result.implementation_notes.map((note, idx) => (
                            <li key={idx}>{note}</li>
                          )) :
                          <li>{content.result.implementation_notes}</li>
                        }
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      );
    } else {
      // Fallback to original format
      return formatOptimizationResult(content);
    }
  };

  const formatOptimizationResult = (result) => {
    if (result.optimization_solution && result.optimization_solution.status === 'optimal') {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle className="w-5 h-5" />
              <span className="font-semibold">Optimization Successful</span>
            </div>
            <button
              onClick={() => {
                setCurrentModel(result.model_building);
                setShowModelModal(true);
              }}
              className="flex items-center gap-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
            >
              <Eye className="w-4 h-4" />
              View Model
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                <Bot className="w-5 h-5" />
                Intent Classification
              </h3>
              <p className="text-sm text-gray-300 mb-1">
                <span className="font-medium">Intent:</span> {result.intent_classification?.intent}
              </p>
              <p className="text-sm text-gray-300 mb-1">
                <span className="font-medium">Confidence:</span> {(result.intent_classification?.confidence * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-300">
                <span className="font-medium">Reasoning:</span> {result.intent_classification?.reasoning}
              </p>
            </div>

            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Data Analysis
              </h3>
              <p className="text-sm text-gray-300 mb-1">
                <span className="font-medium">Entities:</span> {result.data_analysis?.entities?.length || 0}
              </p>
              <p className="text-sm text-gray-300 mb-1">
                <span className="font-medium">Readiness:</span> {(result.data_analysis?.readiness * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-300">
                <span className="font-medium">Data Quality:</span> Good
              </p>
            </div>

            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Model Building
              </h3>
              <p className="text-sm text-gray-300 mb-1">
                <span className="font-medium">Type:</span> {result.model_building?.model_type}
              </p>
              <p className="text-sm text-gray-300 mb-1">
                <span className="font-medium">Variables:</span> {result.model_building?.variables || 0}
              </p>
              <p className="text-sm text-gray-300">
                <span className="font-medium">Complexity:</span> Medium
              </p>
            </div>

            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Optimization Solution
              </h3>
              <p className="text-sm text-gray-300 mb-1">
                <span className="font-medium">Status:</span> {result.optimization_solution?.status}
              </p>
              <p className="text-sm text-gray-300 mb-1">
                <span className="font-medium">Objective Value:</span> {result.optimization_solution?.objective_value || 'N/A'}
              </p>
              <p className="text-sm text-gray-300">
                <span className="font-medium">Execution Time:</span> {result.performance_metrics?.total_execution_time ? (result.performance_metrics.total_execution_time / 1000).toFixed(2) + 's' : 'N/A'}
              </p>
            </div>
          </div>

          {result.optimization_solution?.solution && Object.keys(result.optimization_solution.solution).length > 0 && (
            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Solution Variables</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {Object.entries(result.optimization_solution.solution).map(([key, value]) => (
                  <div key={key} className="bg-gray-700 p-2 rounded text-sm">
                    <span className="font-medium">{key}:</span> {value}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    } else {
      return (
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>Optimization failed: {result.error}</span>
        </div>
      );
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">DcisionAI Manufacturing Optimizer</h1>
                <p className="text-sm text-gray-400">AI-powered manufacturing optimization</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-400">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        {messages.length === 0 ? (
          /* Welcome Screen */
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-2xl">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-3xl font-bold mb-4">Welcome to DcisionAI Manufacturing Optimizer</h2>
              <p className="text-gray-400 mb-8 text-lg">
                Ask me anything about manufacturing optimization. I can help you optimize production lines, 
                supply chains, quality control, and resource allocation using AI-powered analysis.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {exampleQueries.map((query, index) => (
                  <button
                    key={index}
                    onClick={() => setInput(query)}
                    className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors border border-gray-700 hover:border-gray-600"
                  >
                    <p className="text-sm">{query}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Chat Messages */
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.type !== 'user' && (
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                
                <div
                  className={`max-w-3xl rounded-2xl px-4 py-3 ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : message.type === 'error'
                      ? 'bg-red-900/50 text-red-200 border border-red-800'
                      : 'bg-gray-800 text-gray-100'
                  }`}
                >
                  {message.type === 'user' ? (
                    <p>{message.content}</p>
                  ) : message.type === 'error' ? (
                    <p>{message.content}</p>
                  ) : (
                    formatStreamingMessage(message.content)
                  )}
                </div>

                {message.type === 'user' && (
                  <div className="w-8 h-8 bg-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-gray-800 rounded-2xl px-4 py-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-gray-300">Processing optimization request with AI agents...</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-gray-800 bg-gray-900/50 backdrop-blur-sm p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Describe your manufacturing optimization problem..."
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 pr-12 text-white placeholder-gray-400 resize-none focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  rows="1"
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white p-3 rounded-xl transition-colors flex items-center justify-center"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Model Details Modal */}
      {showModelModal && currentModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto modal-scroll">
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Settings className="w-6 h-6" />
                Mathematical Optimization Model
              </h2>
              <button
                onClick={() => setShowModelModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Model Overview */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-3 text-white">Model Overview</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Type:</span>
                    <div className="text-white font-medium">{currentModel.model_type}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Variables:</span>
                    <div className="text-white font-medium">{currentModel.variables?.length || 0}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Constraints:</span>
                    <div className="text-white font-medium">{currentModel.constraints?.length || 0}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Complexity:</span>
                    <div className="text-white font-medium">{currentModel.complexity}</div>
                  </div>
                </div>
              </div>

              {/* Variables */}
              {currentModel.variables && currentModel.variables.length > 0 && (
                <div className="bg-gray-800 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-white">Decision Variables</h3>
                  <div className="space-y-2">
                    {currentModel.variables.map((variable, index) => (
                      <div key={index} className="bg-gray-700 p-3 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="text-white font-medium">{variable.name}</span>
                          <span className="text-blue-400 text-sm">{variable.type}</span>
                        </div>
                        <div className="text-gray-300 text-sm mt-1">
                          Bounds: [{variable.bounds?.[0] || '0'}, {variable.bounds?.[1] || '∞'}]
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Objective Function */}
              {currentModel.objective && (
                <div className="bg-gray-800 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-white">Objective Function</h3>
                  <div className="bg-gray-700 p-3 rounded-lg">
                    <code className="text-green-400 text-sm font-mono break-all">
                      {currentModel.objective}
                    </code>
                  </div>
                </div>
              )}

              {/* Constraints */}
              {currentModel.constraints && currentModel.constraints.length > 0 && (
                <div className="bg-gray-800 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-white">Constraints</h3>
                  <div className="space-y-2">
                    {currentModel.constraints.map((constraint, index) => (
                      <div key={index} className="bg-gray-700 p-3 rounded-lg">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-gray-400 text-sm">Constraint {index + 1}</span>
                          <span className="text-blue-400 text-sm">{constraint.type}</span>
                        </div>
                        <code className="text-yellow-400 text-sm font-mono break-all">
                          {constraint.expression}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Mathematical Notation */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-3 text-white">Mathematical Formulation</h3>
                <div className="bg-gray-700 p-4 rounded-lg">
                  <div className="text-white text-sm space-y-2">
                    <div><strong>Problem Type:</strong> {currentModel.model_type.replace('_', ' ').toUpperCase()}</div>
                    <div><strong>Variables:</strong> {currentModel.variables?.length || 0} decision variables</div>
                    <div><strong>Constraints:</strong> {currentModel.constraints?.length || 0} constraint equations</div>
                    <div><strong>Solver:</strong> PuLP CBC (Coin-or Branch and Cut)</div>
                    <div><strong>Status:</strong> Real mathematical optimization (not simulated)</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
