## Mapilio Kit

Mapilio Kit is a library for processing and uploading images to [Mapilio](https://www.mapilio.com/).
<!DOCTYPE html>


<h2>Kit Contents</h2>
<ul>
  <li><a href="#introduction">Introduction</a></li>
  <li><a href="#getting-started">Getting Started</a></li>
  <li><a href="#usage">Usage</a></li>
  <li><a href="#contributing">Contributing</a></li>
  <li><a href="#license">License</a></li>
  <li><a href="#to-do">To-Do</a></li>
</ul>

<hr>

<h2 id="introduction">Introduction</h2>

<p>Our Image Uploader with GPS Metadata is a powerful tool designed to simplify the process of uploading and managing images, while also preserving and utilizing valuable location-based information embedded in photos. With the increasing popularity of geotagging in modern cameras and smartphones, GPS metadata in images can provide valuable context and enhance the user experience. Whether you're a photographer, a traveler, or simply someone who values the story behind each image, our uploader has you covered.
<hr>

<h2 id="getting-started">Getting Started</h2>

<p>These instructions will help contributors get a copy of your project up and running on their local machine for development and testing purposes.</p>

<ol>
  <li><strong>Prerequisites:</strong>
    <p>To upload images to Mapilio, an account is required and can be created <a href="https://www.mapilio.com/signup" target="_blank">here</a>. When
    using the kits for the first time, user authentication is required. You will be prompted to enter your account
    credentials.</p>
  </li>
  <li><strong>Installation:</strong>
    <p>via Pip on Ubuntu + 18.04 and Python (3.6 and above) and git are required:</p>
    <pre><code># Installation commands
git clone git@github.com:mapilio/mapilio-kit-v2.git
cd mapilio-kit-v2
chmod +x install.sh
source ./install.sh
pip install -r requirements.txt 
</code></pre>
  </li>
</ol>

<hr>

<h2 id="usage">Usage</h2>
<hr>

<h3>User Authentication</h3>

<p>To upload images to mapilio, an account is required and can be created <a href="https://www.mapilio.com/signup" target="_blank">here</a>. When using the tools for the first time, user authentication is required. You will be prompted to enter your account credentials.</p>
<h4>Examples</h4>
<p>Authenticate new user:</p>
<pre><code>mapilio_kit authenticate
</code></pre>
<p>Authenticate for user `user_name`. If the user is already authenticated, it will update the credentials in the config:</p>
<pre><code>mapilio_kit authenticate --user_name "mapilio_user_mail"
</code></pre>
<hr>

<h2 id="contributing">Contributing</h2>

<p>We welcome contributions from the community! If you'd like to contribute to the project, please follow these guidelines:</p>

<ol>
  <li><strong>Fork the Repository:</strong>
    <p>Fork this repository to your own GitHub account.</p>
  </li>
  <li><strong>Create a Branch:</strong>
    <p>Create a new branch for your feature or bug fix.</p>
    <pre><code>git checkout -b feature/your-feature</code></pre>
  </li>
  <li><strong>Make Changes:</strong>
    <p>Make your changes to the codebase. Be sure to follow the project's coding style and conventions.</p>
  </li>
  <li><strong>Commit Changes:</strong>
    <p>Commit your changes with clear and descriptive commit messages.</p>
    <pre><code>git commit -m "Add feature: your feature description"</code></pre>
  </li>
  <li><strong>Push Changes:</strong>
    <p>Push your changes to your forked repository on GitHub.</p>
    <pre><code>git push origin feature/your-feature</code></pre>
  </li>
  <li><strong>Open a Pull Request:</strong>
    <p>Open a pull request from your forked repository to the original repository. Provide a clear and detailed description of your changes.</p>
  </li>
  <li><strong>Code Review:</strong>
    <p>Be open to feedback and participate in the code review process. Address any comments or suggestions from maintainers.</p>
  </li>
  <li><strong>Merge:</strong>
    <p>Once your pull request is approved, it will be merged into the main project. Congratulations, you've contributed to the project!</p>
  </li>
</ol>

<hr>

<h2 id="license">License</h2>

<p>This project is licensed under the MIT LICENSE - see the <code>LICENSE.md</code> file for details.</p>

<hr>
