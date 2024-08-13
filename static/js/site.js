// const sleep = ms => new Promise(r => setTimeout(r, ms));
// async function syncsleep(ms) {
//     await sleep(ms);
// }

document.addEventListener("DOMContentLoaded", function(event) {
    fetch('http://52.172.33.78:5000/podcasts/1/episodes')
        .then(response => response.json())
        .then(data => {
            let episodes = document.querySelector('#episodes');
            data.forEach(episode => {
                let a = document.createElement('a');
                a.href = "#";
                a.classList.add('list-group-item', 'list-group-item-action');
                a.innerText = `#${episode.id}: ${episode.title}`;
                a.dataset.id = episode.id;
                a.onclick = function(e) {
                    e.preventDefault();
                    document.querySelectorAll('#episodes a').forEach(node => {
                        node.classList.remove('active');
                        node.ariaCurrent = 'false';
                        document.querySelector('#suggestedQs div').innerText = '';
                    });
                    a.classList.add('active');
                    a.ariaCurrent = 'true';
                    fetch(`http://52.172.33.78:5000/podcasts/1/episodes/${episode.id}`)
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
                                    document.querySelector('#question').value = q;
                                    document.querySelector('#btnAnswerMe').click();
                                });
                            });
                        });
                };
                episodes.appendChild(a);
            });
            episodes.firstElementChild.click();

            let btnAnswerMe = document.querySelector('#btnAnswerMe');
            btnAnswerMe.addEventListener('click', function(e) {
                e.preventDefault();
                document.querySelector('#answer').dataset.answer = '';
                let q = document.querySelector('#question').value;
                let eid = document.querySelector("#episodes a.active").dataset.id;
                type=document.querySelector('#ddType').dataset.type;
                let evtSource = new EventSource(`http://52.172.33.78:5000/ask?q=${q}&eid=${eid}&type=${type}`);
                evtSource.onmessage = (event) => {
                    var converter = new showdown.Converter();
                    document.querySelector('#answer').dataset.answer += event.data;
                    document.querySelector('#answer').innerHTML = converter.makeHtml(document.querySelector('#answer').dataset.answer);
                };
                evtSource.onerror = (error) => {
                    evtSource.close();
                };
            });

            document.querySelectorAll(".dropdown-menu li a").forEach(li => {
                li.addEventListener('click', function(e) {
                    document.querySelector('#ddType').innerText = 'Mode: ' + e.target.innerText;
                    console.log(e.target.dataset.value);
                    document.querySelector('#ddType').dataset.type = e.target.dataset.value;
                });
            });

            document.querySelector('#question').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    document.querySelector('#btnAnswerMe').click();
                }
            });
            document.querySelector('#question').addEventListener('focus', function(e) {
                document.querySelector('#question').value = '';
            });
        });
});
