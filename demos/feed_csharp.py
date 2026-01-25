import time
from typing import Any
from xarp.express import AsyncXR, SyncXR
from xarp.server import run, show_qrcode_link

def sync_app(xr: SyncXR, kwargs: dict[str, Any]) -> None:
    xr.baseline_code(
    """
    using UnityEngine;
    public class Example : MonoBehaviour
    {
        void Awake()
        {
            for (int i = 0; i < 2; i++)
            {
                GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
                cube.transform.position = new Vector3(i*2, 0, 2);
                cube.AddComponent<Rotator>();
            }
        }
    }

    public class Rotator : MonoBehaviour
    {
        void Update()
        {
            transform.Rotate(new Vector3(15, 30, 45) * Time.deltaTime);
        }
    }

    var newGameObject = new GameObject("Scenario").AddComponent<Example>();
    var newGameObjectName = newGameObject.name;
    var newGameObjectInstanceId = newGameObject.GetInstanceID();
    var newGameObjectScene = newGameObject.gameObject.scene.name;
    """
    )
    while True:
        stream = xr.sense(head=True)
        try:
            for _ in stream:
                pass
        finally:
            stream.close()
        time.sleep(0.5)



if __name__ == '__main__':
    show_qrcode_link()
    run(sync_app)



"""
        using UnityEngine;

        public class Example : MonoBehaviour
        {
            void Awake()
            {
                for (int i = 0; i < 2; i++)
                {
                    var go = new GameObject("CubeLike_" + i);
                    go.transform.position = new Vector3(i * 2f, 0f, 0f);
                    go.AddComponent<Rotator>();

                    // Optional: build a simple cube mesh without CreatePrimitive (keeps CoreModule-only)
                    var mf = go.AddComponent<MeshFilter>();
                    var mr = go.AddComponent<MeshRenderer>();
                    mf.sharedMesh = BuildCube();
                }
            }

            private static Mesh BuildCube()
            {
                var m = new Mesh();
                m.vertices = new[]
                {
                    new Vector3(-0.5f, -0.5f, -0.5f),
                    new Vector3( 0.5f, -0.5f, -0.5f),
                    new Vector3( 0.5f,  0.5f, -0.5f),
                    new Vector3(-0.5f,  0.5f, -0.5f),
                    new Vector3(-0.5f, -0.5f,  0.5f),
                    new Vector3( 0.5f, -0.5f,  0.5f),
                    new Vector3( 0.5f,  0.5f,  0.5f),
                    new Vector3(-0.5f,  0.5f,  0.5f),
                };

                m.triangles = new[]
                {
                    0,2,1, 0,3,2, // back
                    4,5,6, 4,6,7, // front
                    0,1,5, 0,5,4, // bottom
                    2,3,7, 2,7,6, // top
                    0,4,7, 0,7,3, // left
                    1,2,6, 1,6,5, // right
                };

                m.RecalculateNormals();
                return m;
            }
        }

        public class Rotator : MonoBehaviour
        {
            void Update()
            {
                transform.Rotate(new Vector3(15f, 30f, 45f) * Time.deltaTime);
            }
        }

        var newGameObject = new GameObject("Scenario").AddComponent<Example>();
        var newGameObjectName = newGameObject.name;
        var newGameObjectInstanceId = newGameObject.GetInstanceID();

    """