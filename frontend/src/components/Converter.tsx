import React, { useState } from "react";
import './Converter.css';

const Converter = () => {
  const [url, setUrl] = useState('');
  const [format, setFormat] = useState('mp4');
  const [downloadLink, setDownloadLink] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    if (!url) {
      alert("Please enter a YouTube URL.");
      return;
    }

    setLoading(true);
    setDownloadLink('');

    try {
      const response = await fetch('http://localhost:5000/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, format }),
      });

      const data = await response.json();

      if (data.download_url) {
        setDownloadLink(data.download_url);
      } else {
        alert('Error downloading file.');
      }
    } catch (error) {
      console.error(error);
      alert('Failed to connect to server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="converter-container">
      <h1>YouTube Converter</h1>

      <input
        type="text"
        placeholder="Enter YouTube URL"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="input-url"
      />

      <select
        value={format}
        onChange={(e) => setFormat(e.target.value)}
        className="input-format"
      >
        <option value="mp4">MP4</option>
        <option value="mp3">MP3</option>
      </select>

      <button onClick={handleDownload} className="download-btn" disabled={loading}>
        {loading ? "Downloading..." : "Start Download"}
      </button>

      {downloadLink && (
        <a href={downloadLink} download className="download-link">
          Click here to download
        </a>
      )}
    </div>
  );
};

export default Converter;
