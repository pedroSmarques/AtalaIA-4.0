from ultralytics import YOLO

if __name__ == "__main__":
    # Carrega o modelo base leve (ideal para os 4 GB de VRAM da GTX 1650)
    model = YOLO("yolov8n.pt")

    # Inicia o treinamento usando o dataset exportado do Roboflow
    model.train(
        data="dataset/data.yaml",
        epochs=100,
        imgsz=640,
        batch=8,       # Se der erro de memória (CUDA out of memory), mude para 4
        workers=2,
        device=0       # Usa a sua GeForce GTX 1650
)