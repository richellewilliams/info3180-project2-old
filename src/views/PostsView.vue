<template>
  <div class="about container">
    <h2 class="pb-3">Posts</h2>

    <div class="row row-cols-1">
      <div v-for="post in posts" :key="post.id">
        <div class="card mb-3">
          <div class="card-body">
                <h3 class="card-title">{{ post.user_id }}</h3>
          </div>
            <div class="col-md-4">
              <img :src="post.photo" alt="Post" class="card-img-top">
            </div>
            <div class="col-md-8">
              <div class="card-body">
                <p class="card-text">{{ post.caption }}</p>
              </div>
              <div class="card-body">
                <p class="card-text">{{ post.likes }}</p>
                <p class="card-text">{{ post.created_at }}</p>
              </div>
              
            </div>
            
        </div> 
      </div>
    </div>
    <router-link to="/posts/new">
      <button>New Post</button>
    </router-link>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
let posts = ref([]);

function fetchPosts(){
    fetch('/api/v1/posts')
    .then((response) => response.json())
    .then((data) => {
        console.log(data);
        posts.value = data.data;
    })
    .catch((error) => {
        console.log(error);
    });
}

onMounted(()=> {
    fetchPosts();
});
</script>

<style>
</style>