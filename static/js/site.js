// const sleep = ms => new Promise(r => setTimeout(r, ms));
// async function syncsleep(ms) {
//     await sleep(ms);
// }

document.addEventListener("DOMContentLoaded", function(event) {
    fetch('./podcasts/1/episodes')
        .then(response => response.json())
        .then(data => {
            let episodes = document.querySelector('#episodes');
            data.forEach(episode => {
                let a = document.createElement('a');
                a.href = "#";
                a.classList.add('list-group-item', 'list-group-item-action');
                a.innerText = `#${episode.id}: ${episode.title}`;
                a.onclick = function(e) {
                    e.preventDefault();
                    document.querySelectorAll('#episodes a').forEach(node => {
                        node.classList.remove('active');
                        node.ariaCurrent = 'false';
                        document.querySelector('#suggestedQs div').innerText = '';
                    });
                    a.classList.add('active');
                    a.ariaCurrent = 'true';
                    fetch(`./podcasts/1/episodes/${episode.id}`)
                        .then(response => response.json())
                        .then(data => {
                            document.querySelector('#episode-summary').innerText = data.summary;
                            sample_questions = JSON.parse(data.sample_questions).questions;
                            sample_questions.forEach(q => {
                                let q_node = document.createElement('p');
                                let a_node = document.createElement('a');
                                a_node.href = '#';
                                a_node.innerText = q;
                                q_node.appendChild(a_node);
                                document.querySelector('#suggestedQs div').appendChild(q_node);
                                a_node.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    document.querySelector('#question').innerText = q;
                                    document.querySelector('#answer').innerText = '';
                                    let evtSource = new EventSource(`./ask?q=${q}`);
                                    evtSource.onmessage = (event) => {
                                        document.querySelector('#answer').innerText += event.data;
                                    };
                                    evtSource.onerror = (error) => {
                                        evtSource.close();
                                    };
                                });
                            });
                        });
                };
                episodes.appendChild(a);
            });
            episodes.firstElementChild.click();
        });
});
