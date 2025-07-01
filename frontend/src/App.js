import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

function App() {
  const [scrapers, setScrapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showEditConfigModal, setShowEditConfigModal] = useState(false);
  const [newScraperName, setNewScraperName] = useState('');
  const [newScrapingUrl, setNewScrapingUrl] = useState('');
  const [warning, setWarning] = useState('');
  const [editScraperId, setEditScraperId] = useState(null);
  const [editScraperName, setEditScraperName] = useState('');
  const [editScrapingUrl, setEditScrapingUrl] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [trimOutput, setTrimOutput] = useState('');

  // New states for Refresh output and toggles
  const [refreshOutputHtml, setRefreshOutputHtml] = useState('');
  const [refreshOutputJson, setRefreshOutputJson] = useState(null);
  const [showOutput, setShowOutput] = useState(true);
  const [outputFormatHtml, setOutputFormatHtml] = useState(true); // true=HTML, false=JSON

  // New states for added fields
  const [selectedTags, setSelectedTags] = useState([]);
  const [groupRows, setGroupRows] = useState(0);
  const [rowLabels, setRowLabels] = useState([]);

  // New states for Select Tags modal
  const [showSelectTagsModal, setShowSelectTagsModal] = useState(false);
  const [availableTags, setAvailableTags] = useState([]);
  const [selectedTagIds, setSelectedTagIds] = useState(new Set());

  // New state for Set Labels modal and input values
  const [showSetLabelsModal, setShowSetLabelsModal] = useState(false);
  const [labelInputs, setLabelInputs] = useState([]);

  useEffect(() => {
    fetchScrapers();
  }, []);

  const fetchScrapers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/scrapers`);
      setScrapers(response.data);
    } catch (error) {
      console.error('Error fetching scrapers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this scraper?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/scrapers`, { data: { scraper_id: id } });
      fetchScrapers();
    } catch (error) {
      console.error('Error deleting scraper:', error);
    }
  };

  const openAddModal = () => {
    setWarning('');
    setNewScraperName('');
    setNewScrapingUrl('');
    setShowAddModal(true);
  };

  const closeAddModal = () => {
    setShowAddModal(false);
  };

  const openEditModal = (scraper) => {
    setWarning('');
    setEditScraperId(scraper.scraper_id);
    setEditScraperName(scraper.scraper_name);
    setEditScrapingUrl(scraper.scraping_url);
    setTestResult(null);
    setShowEditModal(true);
  };

  const closeEditModal = () => {
    setShowEditModal(false);
  };

  const isValidUrl = (url) => {
    try {
      new URL(url);
      return true;
    } catch (_) {
      return false;
    }
  };

  const handleAddConfirm = async () => {
    if (!newScraperName.trim() || !newScrapingUrl.trim()) {
      setWarning('Please fill in both Scraper Name and Scraping URL.');
      return;
    }

    if (!isValidUrl(newScrapingUrl.trim())) {
      setWarning('Please enter a valid URL for Scraping URL.');
      return;
    }

    try {
      await axios.post(`${API_BASE_URL}/scrapers`, {
        scraper_name: newScraperName,
        scraping_url: newScrapingUrl
      });
      closeAddModal();
      fetchScrapers();
    } catch (error) {
      console.error('Error creating scraper:', error);
      setWarning('Failed to create scraper. Please try again.');
    }
  };

  const handleEditConfirm = async () => {
    if (!editScraperName.trim() || !editScrapingUrl.trim()) {
      setWarning('Please fill in both Scraper Name and Scraping URL.');
      return;
    }

    if (!isValidUrl(editScrapingUrl.trim())) {
      setWarning('Please enter a valid URL for Scraping URL.');
      return;
    }

    try {
      await axios.put(`${API_BASE_URL}/scrapers`, {
        scraper_id: editScraperId,
        scraper_name: editScraperName,
        scraping_url: editScrapingUrl
      });
      closeEditModal();
      fetchScrapers();
    } catch (error) {
      console.error('Error updating scraper:', error);
      setWarning('Failed to update scraper. Please try again.');
    }
  };

  const handleTestScraper = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/scrape/${editScraperId}`);
      setTestResult(response.data);
    } catch (error) {
      console.error('Error testing scraper:', error);
      setTestResult({ error: 'Failed to test scraper.' });
    }
  };

  const openEditConfigModal = () => {
    setShowEditConfigModal(true);
  };

  const closeEditConfigModal = () => {
    setShowEditConfigModal(false);
  };

  // Function to parse trim output tag like backend parse_trim_input
  const parseTrimOutput = (trim) => {
    const tagMatch = trim.match(/^<(\w+)([^>]*)>/);
    if (!tagMatch) return null;
    const tagName = tagMatch[1];
    const attrString = tagMatch[2].trim();
    const attrs = {};
    if (attrString) {
      const classMatch = attrString.match(/class=["']([^"']+)["']/);
      if (classMatch) {
        attrs.class = classMatch[1].split(' ');
      }
    }
    return { tagName, attrs };
  };

  // Function to filter raw data based on trim output tag
  const filterRawData = (data, trim) => {
    if (!trim || !data) return data;
    const parsed = parseTrimOutput(trim);
    if (!parsed) return data;

    // For simplicity, if rawData is an object with html/text, filter keys containing tagName
    // This is a placeholder; real filtering depends on rawData structure
    if (typeof data === 'object') {
      // Example: filter keys containing tagName
      const filtered = {};
      Object.keys(data).forEach(key => {
        if (key.includes(parsed.tagName)) {
          filtered[key] = data[key];
        }
      });
      return Object.keys(filtered).length > 0 ? filtered : data;
    }
    return data;
  };

  // Fetch scraper config details including new fields
  const fetchScraperConfigDetails = async (scraperId) => {
    try {
      // Fetch scraper to get scraper_config_id
      const scraperRes = await axios.get(`${API_BASE_URL}/scrapers/${scraperId}`);
      const scraperConfigId = scraperRes.data.scraper_config_id;

      // Fetch scraper config
      const configRes = await axios.get(`${API_BASE_URL}/scraper-config/${scraperConfigId}`);
      const config = configRes.data;
      setTrimOutput(config.trim_input || '');
      setGroupRows(config.group_row_count || 1); // default to 1 if falsy

      // Fetch selected tags
      const tagsRes = await axios.get(`${API_BASE_URL}/scraper-config/${scraperConfigId}/tags`);
      setSelectedTags(Array.isArray(tagsRes.data) ? tagsRes.data : []);

      // Fetch row labels
      const rowLabelsRes = await axios.get(`${API_BASE_URL}/scraper-config/${scraperConfigId}/row-labels`);
      // Sort row labels by row_order
      const sortedRowLabels = rowLabelsRes.data.sort((a, b) => a.row_order - b.row_order);
      setRowLabels(sortedRowLabels);

    } catch (error) {
      console.error('Error fetching scraper config details:', error);
      setTrimOutput('');
      setSelectedTags([]);
      setGroupRows(1); // default to 1 on error
      setRowLabels([]);
    }
  };

  // Refresh output by calling /raw endpoint in scraper_routes with optional parameters
  const refreshOutput = async () => {
    if (!editScraperId) return;

    try {
      // Fetch scraper to get scraper_config_id
      const scraperRes = await axios.get(`${API_BASE_URL}/scrapers/${editScraperId}`);
      const scraperConfigId = scraperRes.data.scraper_config_id;

      // Prepare optional parameters
      const params = {};
      if (trimOutput) params.trim_tag = trimOutput;
      if (groupRows) params.group_row_count = groupRows;

      // Send tags and row_labels as repeated parameters without square brackets
      if (selectedTags.length > 0) {
        selectedTags.forEach((tag) => {
          if (!params.tags) params.tags = [];
          params.tags.push(tag.tag);
        });
      }
      if (rowLabels.length > 0) {
        rowLabels.forEach((label) => {
          if (!params.row_labels) params.row_labels = [];
          params.row_labels.push(label.row_label);
        });
      }

      // Call /raw endpoint with json output
      const jsonRes = await axios.get(`${API_BASE_URL}/raw/${editScraperId}`, { params: { ...params, output_format: 'json' } });
      setRefreshOutputJson(jsonRes.data);

      // Call /raw endpoint with html output
      const htmlRes = await axios.get(`${API_BASE_URL}/raw/${editScraperId}`, { params: { ...params, output_format: 'html' } });
      setRefreshOutputHtml(htmlRes.data || '');

    } catch (error) {
      console.error('Error refreshing output:', error);
      setRefreshOutputJson(null);
      setRefreshOutputHtml('');
    }
  };

  // Call fetchScraperConfigDetails when Edit Configuration modal opens
  useEffect(() => {
    if (showEditConfigModal && editScraperId) {
      fetchScraperConfigDetails(editScraperId);
    }
  }, [showEditConfigModal, editScraperId]);

  // Fetch available tags when Select Tags modal opens
  useEffect(() => {
    if (showSelectTagsModal && editScraperId) {
      const fetchTags = async () => {
        try {
          const params = {};
          if (trimOutput) params.trim_tag = trimOutput;
          const res = await axios.get(`${API_BASE_URL}/raw/${editScraperId}/tags`, { params });
          const tags = res.data.tags || [];
          const descendentTags = res.data.descendent_tags || [];
          // Combine tags and descendent tags
          const combinedTags = [...tags, ...descendentTags];

          // Remove duplicates by tag name
          const uniqueTagsMap = new Map();
          combinedTags.forEach(t => {
            if (!uniqueTagsMap.has(t.tag)) {
              uniqueTagsMap.set(t.tag, t);
            }
          });
          const uniqueTags = Array.from(uniqueTagsMap.values());

          // Calculate occurrences for each tag
          const occurrencesMap = new Map();
          uniqueTags.forEach(t => {
            const count = res.data.raw_html ? (res.data.raw_html.match(new RegExp(`<${t.tag}[^>]*>`, 'g')) || []).length : 0;
            occurrencesMap.set(t.tag, count);
          });

          // Add occurrences to each tag object
          const tagsWithOccurrences = uniqueTags.map(t => ({ ...t, occurrences: occurrencesMap.get(t.tag) || 0 }));

          setAvailableTags(tagsWithOccurrences);

          // Initialize selectedTagIds from current selectedTags
          const currentSelected = new Set(selectedTags.map(t => t.tag));
          setSelectedTagIds(currentSelected);
        } catch (error) {
          console.error('Error fetching available tags:', error);
          setAvailableTags([]);
        }
      };
      fetchTags();
    }
  }, [showSelectTagsModal, editScraperId]);

  const toggleTagSelection = (tag) => {
    const newSelected = new Set(selectedTagIds);
    if (newSelected.has(tag)) {
      newSelected.delete(tag);
    } else {
      newSelected.add(tag);
    }
    setSelectedTagIds(newSelected);
  };

  const confirmTagSelection = () => {
    // Update selectedTags state with selected tags
    const newSelectedTags = availableTags.filter(t => selectedTagIds.has(t.tag)).map(t => ({ tag: t.tag }));
    setSelectedTags(Array.isArray(newSelectedTags) ? newSelectedTags : []);
    setShowSelectTagsModal(false);
  };

  const cancelTagSelection = () => {
    setShowSelectTagsModal(false);
  };

  // Open Set Labels modal and initialize inputs based on groupRows
  const openSetLabelsModal = () => {
    const count = groupRows > 0 ? groupRows : 1;
    const inputs = [];
    for (let i = 0; i < count; i++) {
      inputs.push(rowLabels[i]?.row_label || '');
    }
    setLabelInputs(inputs);
    setShowSetLabelsModal(true);
  };

  // Handle input change in Set Labels modal
  const handleLabelInputChange = (index, value) => {
    const newInputs = [...labelInputs];
    newInputs[index] = value;
    setLabelInputs(newInputs);
  };

  // Confirm Set Labels modal and update rowLabels state
  const confirmSetLabels = () => {
    const newRowLabels = labelInputs.map((label, index) => ({ row_order: index + 1, row_label: label }));
    setRowLabels(newRowLabels);
    setShowSetLabelsModal(false);
  };

  // Cancel Set Labels modal
  const cancelSetLabels = () => {
    setShowSetLabelsModal(false);
  };

  const handleConfirmConfig = async () => {
    if (!editScraperId) return;

    try {
      // Fetch scraper to get scraper_config_id
      const scraperRes = await axios.get(`${API_BASE_URL}/scrapers/${editScraperId}`);
      const scraperConfigId = scraperRes.data.scraper_config_id;

      // Update scraper config
      await axios.put(`${API_BASE_URL}/scraper-config/${scraperConfigId}`, {
        trim_input: trimOutput,
        group_row_count: groupRows
      });

      // Delete existing tags and post new tags
      await axios.delete(`${API_BASE_URL}/scraper-config/${scraperConfigId}/tags`);
      if (selectedTags.length > 0) {
        await axios.post(`${API_BASE_URL}/scraper-config/${scraperConfigId}/tags`, {
          tag: selectedTags.map(tag => tag.tag)
        });
      }

      // Delete existing row labels and post new row labels
      await axios.delete(`${API_BASE_URL}/scraper-config/${scraperConfigId}/row-labels`);
      if (rowLabels.length > 0) {
        await axios.post(`${API_BASE_URL}/scraper-config/${scraperConfigId}/row-labels`, {
          row_order: rowLabels.map((label, index) => index),
          row_label: rowLabels.map(label => label.row_label)
        });
      }

      setShowEditConfigModal(false);
    } catch (error) {
      console.error('Error saving scraper config:', error);
      alert('Failed to save configuration. Please try again.');
    }
  };

  return (
    <>
      <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
        <h1>Scraper API</h1>
        <button onClick={openAddModal} style={{ marginBottom: '20px', padding: '10px 15px', fontSize: '16px' }}>
          Add New Scraper
        </button>
        <button onClick={fetchScrapers} style={{ marginBottom: '20px', padding: '10px 15px', fontSize: '16px', marginLeft: '10px' }}>
          Refresh Scraper List
        </button>
        {loading ? (
          <p>Loading scrapers...</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ccc' }}>
                <th style={{ textAlign: 'left', padding: '8px' }}>Scraper Name</th>
                <th style={{ textAlign: 'left', padding: '8px' }}>Scraping URL</th>
                <th style={{ textAlign: 'left', padding: '8px' }}>Created On</th>
                <th style={{ textAlign: 'left', padding: '8px' }}>Last Updated On</th>
                <th style={{ textAlign: 'left', padding: '8px' }}>Options</th>
              </tr>
            </thead>
            <tbody>
              {scrapers.map(scraper => (
                <tr key={scraper.scraper_id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '8px' }}>{scraper.scraper_name}</td>
                  <td style={{ padding: '8px' }}>{scraper.scraping_url}</td>
                  <td style={{ padding: '8px' }}>{scraper.created_on}</td>
                  <td style={{ padding: '8px' }}>{scraper.last_scraped_on || 'N/A'}</td>
                  <td style={{ padding: '8px' }}>
                    <button onClick={() => openEditModal(scraper)} style={{ marginRight: '10px' }}>
                      Edit
                    </button>
                    <button onClick={() => handleDelete(scraper.scraper_id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Add New Scraper Modal */}
        {showAddModal && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'
          }}>
            <div style={{ backgroundColor: 'white', padding: 20, borderRadius: 5, width: 400 }}>
              <h2>Add New Scraper</h2>
              {warning && <p style={{ color: 'red' }}>{warning}</p>}
              <div>
                <label>Scraper Name:</label><br />
                <input
                  type="text"
                  value={newScraperName}
                  onChange={(e) => setNewScraperName(e.target.value)}
                  style={{ width: '100%', marginBottom: 10 }}
                />
              </div>
              <div>
                <label>Scraping URL:</label><br />
                <input
                  type="text"
                  value={newScrapingUrl}
                  onChange={(e) => setNewScrapingUrl(e.target.value)}
                  style={{ width: '100%', marginBottom: 10 }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={closeAddModal} style={{ marginRight: 10 }}>
                  Cancel
                </button>
                <button onClick={handleAddConfirm}>
                  Confirm
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Scraper Modal */}
        {showEditModal && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'
          }}>
            <div style={{ backgroundColor: 'white', padding: 20, borderRadius: 5, width: 500 }}>
              <h2>Edit Scraper</h2>
              {warning && <p style={{ color: 'red' }}>{warning}</p>}
              <div>
                <label>Scraper Name:</label><br />
                <input
                  type="text"
                  value={editScraperName}
                  onChange={(e) => setEditScraperName(e.target.value)}
                  style={{ width: '100%', marginBottom: 10 }}
                />
              </div>
              <div>
                <label>Scraping URL:</label><br />
                <input
                  type="text"
                  value={editScrapingUrl}
                  onChange={(e) => setEditScrapingUrl(e.target.value)}
                  style={{ width: '100%', marginBottom: 10 }}
                />
              </div>
              <div style={{ display: 'flex', gap: '10px', marginBottom: 10 }}>
                <button onClick={handleTestScraper}>
                  Test Scraper
                </button>
                <button onClick={openEditConfigModal}>
                  Edit Configuration
                </button>
              </div>
              {testResult && (
                <pre style={{ backgroundColor: '#eee', padding: 10, maxHeight: 200, overflowY: 'auto' }}>
                  {typeof testResult === 'object' ? JSON.stringify(testResult, null, 2) : testResult}
                </pre>
              )}
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={closeEditModal} style={{ marginRight: 10 }}>
                  Cancel
                </button>
                <button onClick={handleEditConfirm}>
                  Confirm
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Configuration Modal */}
        {showEditConfigModal && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'
          }}>
            <div style={{ backgroundColor: 'white', padding: 20, borderRadius: 5, width: 600, maxHeight: '80vh', overflowY: 'auto' }}>
              <h2>Edit Configuration</h2>
              <div style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: '10px' }}>
                <label>Trim Output:</label>
                <input
                  type="text"
                  value={trimOutput}
                  onChange={(e) => setTrimOutput(e.target.value)}
                  placeholder="Enter tag to trim output, e.g. <div class='content'>"
                  style={{ flexGrow: 1 }}
                />
              </div>

              <div style={{ marginBottom: 10 }}>
                <label>Selected Tags:</label>
                <ul style={{ maxHeight: '100px', overflowY: 'auto', border: '1px solid #ccc', padding: '5px' }}>
                  {selectedTags.map(tag => (
                    <li key={tag.tag}>{tag.tag}</li>
                  ))}
                </ul>
              </div>

              <div style={{ marginBottom: 10 }}>
                <label>Group Rows:</label>
                <input
                  type="number"
                  value={groupRows}
                  onChange={(e) => setGroupRows(Number(e.target.value))}
                  style={{ width: '100px' }}
                />
              </div>

              <div style={{ marginBottom: 10 }}>
                <label>Row Labels:</label>
                <ol style={{ maxHeight: '150px', overflowY: 'auto', border: '1px solid #ccc', padding: '5px' }}>
                  {rowLabels.map(label => (
                    <li key={label.scraper_config_row_label_id}>
                      {label.row_order}. {label.row_label}
                    </li>
                  ))}
                </ol>
              </div>

              {/* New toggles and buttons */}
              <div style={{ display: 'flex', gap: '10px', marginBottom: 10 }}>
                <button onClick={() => setOutputFormatHtml(!outputFormatHtml)}>
                  {outputFormatHtml ? 'HTML' : 'JSON'}
                </button>
                <button onClick={() => setShowOutput(!showOutput)}>
                  {showOutput ? 'Hide' : 'Show'}
                </button>
                <button onClick={refreshOutput}>
                  Refresh
                </button>             
                <button onClick={() => setShowSelectTagsModal(true)}>
                  Select Tags
                </button>
                <button onClick={openSetLabelsModal}>
                  Set Labels
                </button>
              </div>

              {/* Output display box */}
              {showOutput && (
                <pre style={{ backgroundColor: '#eee', padding: 10, maxHeight: 200, overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                  {outputFormatHtml ? refreshOutputHtml : JSON.stringify(refreshOutputJson, null, 2)}
                </pre>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button onClick={handleConfirmConfig}>
                  Confirm
                </button>
                <button onClick={closeEditConfigModal}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Select Tags Modal */}
        {showSelectTagsModal && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'
          }}>
            <div style={{ backgroundColor: 'white', padding: 20, borderRadius: 5, width: '90vw', maxHeight: '80vh', overflowY: 'auto' }}>
              <h2>Select Tags</h2>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ border: '1px solid #ccc', padding: '8px', width: '25%' }}>Tag</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px' }}>Occurrences</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px', width: '35%' }}>Example Output</th>
                    <th style={{ border: '1px solid #ccc', padding: '8px' }}>Select Tag</th>
                  </tr>
                </thead>
                <tbody>
                  {availableTags.map((tag) => (
                    <tr key={tag.tag}>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{tag.tag}</td>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{tag.count}</td>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>{tag.example_output}</td>
                      <td style={{ border: '1px solid #ccc', padding: '8px' }}>
                        <input
                          type="checkbox"
                          checked={selectedTagIds.has(tag.tag)}
                          onChange={() => toggleTagSelection(tag.tag)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button onClick={cancelTagSelection}>Cancel</button>
                <button onClick={confirmTagSelection}>Confirm</button>
              </div>
            </div>
          </div>
        )}

        {/* Set Labels Modal */}
        {showSetLabelsModal && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'
          }}>
            <div style={{ backgroundColor: 'white', padding: 20, borderRadius: 5, width: 400, maxHeight: '80vh', overflowY: 'auto' }}>
              <h2>Set Labels</h2>
              <ol style={{ paddingLeft: '20px' }}>
                {labelInputs.map((value, index) => (
                  <li key={`label-input-${index}`} style={{ marginBottom: '10px' }}>
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => handleLabelInputChange(index, e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </li>
                ))}
              </ol>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button onClick={cancelSetLabels}>Cancel</button>
                <button onClick={confirmSetLabels}>Confirm</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default App;
